/*
 * NEA28V1 Premium Tier Interface
 *
 * Responsibilities:
 * - Monthly / annual pricing display
 * - Tier recommendation engine
 * - Tier selection handling
 * - Premium tier navigation
 * - Pricing state management
 *
 * Payment URLs intentionally remain configurable.
 */

(function () {
  "use strict";

  const CONFIG = {
    defaultBilling: "monthly",

    checkoutUrls: {
      foundation: {
        monthly: "#",
        annual: "#"
      },

      active: {
        monthly: "#",
        annual: "#"
      },

      professional: {
        monthly: "#",
        annual: "#"
      },

      elite: {
        monthly: "#",
        annual: "#"
      }
    },

    recommendations: {
      beginner: {
        tier: "foundation",
        title: "Foundation — $29/month",
        text:
          "Foundation is designed for traders building a structured process who want an affordable entry point into recurring NEA28V1 trade opportunities."
      },

      active: {
        tier: "active",
        title: "Active — $59/month",
        text:
          "Active is designed for traders who regularly participate in the market and want NEA28V1 integrated into their daily trading workflow."
      },

      professional: {
        tier: "professional",
        title: "Professional — $99/month",
        text:
          "Professional is designed for serious traders who want broader opportunity coverage, deeper analysis, and more advanced trade intelligence."
      },

      funded: {
        tier: "elite",
        title: "Elite — $199/month",
        text:
          "Elite is designed for advanced, high-activity, funded-account, and substantial-capital traders who want the broadest available NEA28V1 intelligence environment."
      }
    }
  };

  let billingMode = CONFIG.defaultBilling;


  function initialize() {
    initializeBilling();
    initializeProfiles();
    initializeTierSelection();
    updatePricing();
  }


  function initializeBilling() {
    const monthlyButton = document.getElementById("monthlyBilling");
    const annualButton = document.getElementById("annualBilling");

    if (!monthlyButton || !annualButton) {
      return;
    }

    monthlyButton.addEventListener("click", function () {
      setBillingMode("monthly");
    });

    annualButton.addEventListener("click", function () {
      setBillingMode("annual");
    });
  }


  function setBillingMode(mode) {
    if (mode !== "monthly" && mode !== "annual") {
      return;
    }

    billingMode = mode;

    updateBillingButtons();
    updatePricing();
    updateRecommendationPricing();

    const message = document.getElementById("billingMessage");

    if (message) {
      if (mode === "annual") {
        message.textContent =
          "Annual billing provides approximately two months free compared with twelve monthly payments.";
      } else {
        message.textContent =
          "Monthly billing provides maximum flexibility.";
      }
    }
  }


  function updateBillingButtons() {
    const monthlyButton = document.getElementById("monthlyBilling");
    const annualButton = document.getElementById("annualBilling");

    if (monthlyButton) {
      monthlyButton.classList.toggle(
        "active",
        billingMode === "monthly"
      );
    }

    if (annualButton) {
      annualButton.classList.toggle(
        "active",
        billingMode === "annual"
      );
    }
  }


  function updatePricing() {
    const tiers = document.querySelectorAll(".premium-tier");

    tiers.forEach(function (tier) {
      const monthlyPrice = Number(
        tier.dataset.monthly
      );

      const annualPrice = Number(
        tier.dataset.annual
      );

      const priceElement = tier.querySelector(".tier-price");
      const periodElement = tier.querySelector(".billing-period");
      const savingsElement = tier.querySelector(".annual-savings");

      if (!priceElement) {
        return;
      }

      if (billingMode === "annual") {
        priceElement.textContent =
          formatCurrency(annualPrice);

        if (periodElement) {
          periodElement.textContent =
            "per year";
        }

        if (savingsElement) {
          savingsElement.textContent =
            "Save " +
            formatCurrency(
              (monthlyPrice * 12) - annualPrice
            ) +
            " compared with monthly billing.";
        }
      } else {
        priceElement.textContent =
          formatCurrency(monthlyPrice);

        if (periodElement) {
          periodElement.textContent =
            "per month";
        }

        if (savingsElement) {
          savingsElement.textContent =
            "Annual billing available — save approximately two months.";
        }
      }
    });
  }


  function initializeProfiles() {
    const profiles = document.querySelectorAll(
      ".tier-profile"
    );

    profiles.forEach(function (profile) {
      profile.addEventListener("click", function () {

        const profileType =
          profile.dataset.profile;

        showRecommendation(profileType);

        profiles.forEach(function (item) {
          item.classList.remove("selected");
        });

        profile.classList.add("selected");
      });
    });
  }


  function showRecommendation(profileType) {
    const recommendation =
      CONFIG.recommendations[profileType];

    if (!recommendation) {
      return;
    }

    const container =
      document.getElementById(
        "tierRecommendation"
      );

    const title =
      document.getElementById(
        "recommendationTitle"
      );

    const text =
      document.getElementById(
        "recommendationText"
      );

    const button =
      document.getElementById(
        "recommendationButton"
      );

    if (!container || !title || !text || !button) {
      return;
    }

    title.textContent =
      getRecommendationTitle(
        recommendation.tier
      );

    text.textContent =
      recommendation.text;

    button.dataset.tier =
      recommendation.tier;

    container.hidden = false;

    container.scrollIntoView({
      behavior: "smooth",
      block: "center"
    });
  }


  function getRecommendationTitle(tier) {
    const tierElement =
      document.querySelector(
        '.premium-tier[data-tier="' +
        tier +
        '"]'
      );

    if (!tierElement) {
      return "Recommended Premium Tier";
    }

    const tierName =
      tierElement.querySelector("span");

    const price =
      tierElement.querySelector(".tier-price");

    if (!tierName || !price) {
      return "Recommended Premium Tier";
    }

    return (
      tierName.textContent.trim() +
      " — " +
      price.textContent.trim() +
      (
        billingMode === "annual"
          ? "/year"
          : "/month"
      )
    );
  }


  function updateRecommendationPricing() {
    const container =
      document.getElementById(
        "tierRecommendation"
      );

    const button =
      document.getElementById(
        "recommendationButton"
      );

    if (!container || !button || container.hidden) {
      return;
    }

    const tier =
      button.dataset.tier;

    if (tier) {
      const profile =
        Object.keys(
          CONFIG.recommendations
        ).find(function (key) {
          return (
            CONFIG.recommendations[key].tier ===
            tier
          );
        });

      if (profile) {
        showRecommendationWithoutScroll(profile);
      }
    }
  }


  function showRecommendationWithoutScroll(profileType) {
    const recommendation =
      CONFIG.recommendations[profileType];

    if (!recommendation) {
      return;
    }

    const title =
      document.getElementById(
        "recommendationTitle"
      );

    const button =
      document.getElementById(
        "recommendationButton"
      );

    if (!title || !button) {
      return;
    }

    title.textContent =
      getRecommendationTitle(
        recommendation.tier
      );

    button.dataset.tier =
      recommendation.tier;
  }


  function initializeTierSelection() {
    const buttons =
      document.querySelectorAll(
        ".tier-select"
      );

    buttons.forEach(function (button) {

      button.addEventListener(
        "click",
        function (event) {

          event.preventDefault();

          const tier =
            button.dataset.tier;

          selectTier(tier);
        }
      );
    });

    const recommendationButton =
      document.getElementById(
        "recommendationButton"
      );

    if (recommendationButton) {

      recommendationButton.addEventListener(
        "click",
        function () {

          const tier =
            recommendationButton.dataset.tier;

          selectTier(tier);
        }
      );
    }
  }


  function selectTier(tier) {
    if (!CONFIG.checkoutUrls[tier]) {
      return;
    }

    const checkoutUrl =
      CONFIG.checkoutUrls[tier][billingMode];

    if (!checkoutUrl || checkoutUrl === "#") {

      showCheckoutPlaceholder(tier);

      return;
    }

    window.location.href =
      checkoutUrl;
  }


  function showCheckoutPlaceholder(tier) {
    const tierElement =
      document.querySelector(
        '.premium-tier[data-tier="' +
        tier +
        '"]'
      );

    if (!tierElement) {
      return;
    }

    const tierNameElement =
      tierElement.querySelector("span");

    const tierName =
      tierNameElement
        ? tierNameElement.textContent.trim()
        : tier;

    const billing =
      billingMode === "annual"
        ? "annual"
        : "monthly";

    alert(
      "Premium checkout for " +
      tierName +
      " (" +
      billing +
      ") is currently being configured."
    );
  }


  function formatCurrency(value) {
    return new Intl.NumberFormat(
      "en-US",
      {
        style: "currency",
        currency: "USD",
        maximumFractionDigits: 0
      }
    ).format(value);
  }


  document.addEventListener(
    "DOMContentLoaded",
    initialize
  );

})();