(() => {
  "use strict";

  const DATA_URL = "data/community.json";

  const FALLBACK_DISCUSSIONS_URL =
    "https://github.com/0newellgaming0/NEA-Trading-Journal-Analysis-Engine/discussions";

  const $ = (id) => document.getElementById(id);

  function escapeHTML(value) {
    return String(value ?? "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }

  function formatDate(value) {
    if (!value) {
      return "Unknown";
    }

    const date = new Date(value);

    if (Number.isNaN(date.getTime())) {
      return value;
    }

    return new Intl.DateTimeFormat(undefined, {
      year: "numeric",
      month: "short",
      day: "numeric",
      hour: "numeric",
      minute: "2-digit"
    }).format(date);
  }

  function discussionCard(item, featured = false) {
    const category = item.category || "Community";
    const title = item.title || "Untitled discussion";
    const body = item.excerpt || "";
    const comments = Number(item.comments || 0);
    const upvotes = Number(item.upvotes || 0);
    const state = item.closed ? "Closed" : "Open";
    const answer = item.answered ? "Answered" : "";

    return `
      <article class="card community-card${featured ? " featured-discussion" : ""}">

        <div class="card-label">
          ${escapeHTML(category)}
        </div>

        <h3>
          ${escapeHTML(title)}
        </h3>

        <p>
          ${escapeHTML(body)}
        </p>

        <p class="community-meta">
          ${comments}
          comment${comments === 1 ? "" : "s"}

          ${
            upvotes
              ? ` · ${upvotes} upvote${upvotes === 1 ? "" : "s"}`
              : ""
          }

          · ${escapeHTML(state)}

          ${
            answer
              ? ` · ${escapeHTML(answer)}`
              : ""
          }

          · Updated ${escapeHTML(formatDate(item.updatedAt))}
        </p>

        <a
          href="${escapeHTML(item.url || FALLBACK_DISCUSSIONS_URL)}"
          class="card-action"
          target="_blank"
          rel="noopener noreferrer"
        >
          Read Discussion →
        </a>

      </article>
    `;
  }

  function categoryCard(item) {
    const name = item.name || "Community";
    const emoji = item.emoji || "";
    const description =
      item.description || "Community discussion category.";

    const count = Number(item.discussionCount || 0);

    return `
      <article class="card community-category">

        <span>
          ${escapeHTML(emoji)}
          ${escapeHTML(name)}
        </span>

        <strong>
          ${count}
        </strong>

        <p>
          ${escapeHTML(description)}
        </p>

      </article>
    `;
  }

  function render(data) {
    const stats = data.stats || {};

    const featured =
      Array.isArray(data.featured)
        ? data.featured
        : [];

    const recent =
      Array.isArray(data.recent)
        ? data.recent
        : [];

    const categories =
      Array.isArray(data.categories)
        ? data.categories
        : [];


    /*
     * STATISTICS
     */

    if ($("totalDiscussions")) {
      $("totalDiscussions").textContent =
        stats.total ?? 0;
    }

    if ($("questionCount")) {
      $("questionCount").textContent =
        stats.questions ?? 0;
    }

    if ($("ideaCount")) {
      $("ideaCount").textContent =
        stats.ideas ?? 0;
    }

    if ($("categoryCount")) {
      $("categoryCount").textContent =
        stats.categories ?? categories.length;
    }


    /*
     * STATUS
     */

    if ($("communityUpdated")) {
      $("communityUpdated").textContent =
        data.updatedAt
          ? `Updated ${formatDate(data.updatedAt)}`
          : "Community data loaded";
    }

    if ($("statusDot")) {
      $("statusDot").classList.add("online");
    }


    /*
     * FEATURED DISCUSSIONS
     */

    const featuredEl =
      $("featuredDiscussions");

    if (featuredEl) {

      if (featured.length) {

        featuredEl.innerHTML =
          featured
            .map((item) =>
              discussionCard(item, true)
            )
            .join("");

      } else {

        featuredEl.innerHTML = `
          <article class="card">

            <span>
              COMMUNITY
            </span>

            <strong>
              No featured discussions yet
            </strong>

            <p>
              Visit GitHub Discussions to start
              or follow a conversation.
            </p>

          </article>
        `;
      }
    }


    /*
     * RECENT DISCUSSIONS
     */

    const recentEl =
      $("recentDiscussions");

    if (recentEl) {

      if (recent.length) {

        recentEl.innerHTML =
          recent
            .map((item) =>
              discussionCard(item)
            )
            .join("");

      } else {

        recentEl.innerHTML = `
          <article class="card">

            <span>
              COMMUNITY
            </span>

            <strong>
              No recent discussions available
            </strong>

            <p>
              Visit GitHub Discussions for
              the latest activity.
            </p>

          </article>
        `;
      }
    }


    /*
     * CATEGORIES
     */

    const categoriesEl =
      $("categories");

    if (categoriesEl) {

      if (categories.length) {

        categoriesEl.innerHTML =
          categories
            .map((item) =>
              categoryCard(item)
            )
            .join("");

      } else {

        categoriesEl.innerHTML = `
          <article class="card">

            <span>
              COMMUNITY
            </span>

            <strong>
              Categories unavailable
            </strong>

            <p>
              Open GitHub Discussions to view
              the current categories.
            </p>

          </article>
        `;
      }
    }
  }


  /*
   * ERROR STATE
   */

  function renderError() {

    if ($("communityUpdated")) {
      $("communityUpdated").textContent =
        "Community data unavailable";
    }

    if ($("statusDot")) {
      $("statusDot").classList.remove("online");
    }


    const fallback = `
      <article class="card">

        <span>
          GITHUB DISCUSSIONS
        </span>

        <strong>
          Community data is temporarily unavailable
        </strong>

        <p>
          The latest community snapshot could not
          be loaded. You can still access the live
          discussions directly on GitHub.
        </p>

        <a
          href="${FALLBACK_DISCUSSIONS_URL}"
          class="card-action"
          target="_blank"
          rel="noopener noreferrer"
        >
          Open GitHub Discussions →
        </a>

      </article>
    `;


    if ($("featuredDiscussions")) {
      $("featuredDiscussions").innerHTML =
        fallback;
    }

    if ($("recentDiscussions")) {
      $("recentDiscussions").innerHTML =
        fallback;
    }
  }


  /*
   * LOAD COMMUNITY DATA
   */

  async function loadCommunity() {

    try {

      const response =
        await fetch(
          `${DATA_URL}?v=${Date.now()}`,
          {
            cache: "no-store"
          }
        );


      if (!response.ok) {
        throw new Error(
          `HTTP ${response.status}`
        );
      }


      const data =
        await response.json();


      render(data);

    } catch (error) {

      console.error(
        "NEA28V1 community data load failed:",
        error
      );

      renderError();
    }
  }


  /*
   * INITIALIZE
   */

  document.addEventListener(
    "DOMContentLoaded",
    loadCommunity
  );

})();