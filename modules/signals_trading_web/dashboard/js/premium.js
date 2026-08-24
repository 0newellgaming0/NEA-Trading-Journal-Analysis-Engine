"use strict";

const premiumTiers = {

  starter: {
    label: "STARTER PREMIUM",
    title: "Build a Repeatable Trading Process",

    positioning:
      "Designed for traders who are developing a structured process and want recurring access to ranked trade opportunities without paying for an unnecessarily broad intelligence environment.",

    opportunityLevel: "FOCUSED",

    opportunityText:
      "Access a focused selection of ranked opportunities beyond the public Top 10 preview.",

    analysisLevel: "CORE",

    analysisText:
      "Review structured trade information and the core analytical conditions surrounding qualifying opportunities.",

    rankingLevel: "STANDARD",

    rankingText:
      "Compare qualifying opportunities using the NEA28V1 ranking and scoring framework.",

    riskLevel: "CORE",

    riskText:
      "Review entry, stop, target, and risk/reward information associated with qualifying setups.",

    benefitsTitle: "Starter Benefits",

    benefits: [
      "Expanded ranked trade opportunities",
      "Structured trade setups",
      "Entry, stop, target and score information",
      "Core multi-timeframe context",
      "Risk/reward awareness",
      "Recurring access to qualifying opportunities"
    ],

    cta: "VIEW STARTER ACCESS →"
  },


  trader: {
    label: "TRADER PREMIUM",
    title: "Integrate NEA28V1 Into Your Daily Workflow",

    positioning:
      "Designed for active traders who regularly evaluate multiple opportunities and want broader access to the NEA28V1 opportunity pipeline.",

    opportunityLevel: "BROAD",

    opportunityText:
      "Access a substantially broader selection of ranked opportunities across the qualifying market universe.",

    analysisLevel: "EXPANDED",

    analysisText:
      "Evaluate opportunities using broader market context and multiple analytical dimensions.",

    rankingLevel: "ADVANCED",

    rankingText:
      "Use deeper ranking and scoring information to prioritize opportunities and focus attention on stronger candidates.",

    riskLevel: "EXPANDED",

    riskText:
      "Evaluate setups with greater risk, reward, and trade-management context.",

    benefitsTitle: "Trader Benefits",

    benefits: [
      "Broader ranked opportunity coverage",
      "Expanded multi-timeframe analysis",
      "Advanced trade ranking",
      "Structured entry, stop and target information",
      "Expanded risk intelligence",
      "Momentum and market-context analysis",
      "Recurring daily opportunity workflow"
    ],

    cta: "VIEW TRADER ACCESS →"
  },


  professional: {
    label: "PROFESSIONAL PREMIUM",
    title: "Deeper Analysis. Broader Opportunity Coverage.",

    positioning:
      "Designed for serious traders managing significant capital who require broader opportunity coverage and deeper analytical context.",

    opportunityLevel: "VERY BROAD",

    opportunityText:
      "Evaluate a significantly larger portion of the qualifying opportunity pipeline as market conditions evolve.",

    analysisLevel: "ADVANCED",

    analysisText:
      "Access a deeper analytical environment incorporating multiple market-structure, momentum, and confluence perspectives.",

    rankingLevel: "ADVANCED",

    rankingText:
      "Prioritize opportunities using expanded ranking, scoring, and confluence information.",

    riskLevel: "ADVANCED",

    riskText:
      "Evaluate opportunities with deeper risk-management and trade-structure intelligence.",

    benefitsTitle: "Professional Benefits",

    benefits: [
      "Very broad opportunity coverage",
      "Advanced multi-timeframe analysis",
      "Wyckoff analysis",
      "Bill Williams analysis",
      "Elliott Wave analysis",
      "Fibonacci analysis",
      "T-Line analysis",
      "Confluence intelligence",
      "Advanced risk intelligence",
      "Expanded market and event context"
    ],

    cta: "VIEW PROFESSIONAL ACCESS →"
  },


  elite: {
    label: "ELITE PREMIUM",
    title: "The Broadest Available Intelligence Environment",

    positioning:
      "Designed for funded-account traders, high-activity traders, and traders managing substantial capital who require the broadest available NEA28V1 intelligence environment.",

    opportunityLevel: "MAXIMUM",

    opportunityText:
      "Access the broadest available ranked opportunity environment as market conditions evolve throughout the trading cycle.",

    analysisLevel: "MAXIMUM",

    analysisText:
      "Evaluate opportunities across the full analytical stack and broader market context.",

    rankingLevel: "MAXIMUM",

    rankingText:
      "Use the deepest available ranking, scoring, and confluence intelligence to compare the opportunity pipeline.",

    riskLevel: "MAXIMUM",

    riskText:
      "Access the broadest available risk, trade-structure, and trade-management intelligence.",

    benefitsTitle: "Elite Benefits",

    benefits: [
      "Maximum opportunity coverage",
      "Full analytical stack",
      "Multi-timeframe intelligence",
      "Wyckoff analysis",
      "Bill Williams analysis",
      "Elliott Wave analysis",
      "Fibonacci analysis",
      "T-Line analysis",
      "Confluence intelligence",
      "Advanced ranking and scoring",
      "Expanded event and market context",
      "Maximum risk intelligence",
      "Broadest available opportunity monitoring"
    ],

    cta: "VIEW ELITE ACCESS →"
  }

};


function updatePremiumTier(tierKey) {

  const tier = premiumTiers[tierKey];

  if (!tier) {
    return;
  }

  const elements = {

    label: document.getElementById("premiumTierLabel"),

    title: document.getElementById("premiumTierTitle"),

    positioning:
      document.getElementById("premiumTierPositioning"),

    opportunityLevel:
      document.getElementById("premiumOpportunityLevel"),

    opportunityText:
      document.getElementById("premiumOpportunityText"),

    analysisLevel:
      document.getElementById("premiumAnalysisLevel"),

    analysisText:
      document.getElementById("premiumAnalysisText"),

    rankingLevel:
      document.getElementById("premiumRankingLevel"),

    rankingText:
      document.getElementById("premiumRankingText"),

    riskLevel:
      document.getElementById("premiumRiskLevel"),

    riskText:
      document.getElementById("premiumRiskText"),

    benefitsTitle:
      document.getElementById("premiumBenefitsTitle"),

    benefits:
      document.getElementById("premiumBenefits"),

    cta:
      document.getElementById("premiumTierCTA")
  };


  if (elements.label) {
    elements.label.textContent = tier.label;
  }

  if (elements.title) {
    elements.title.textContent = tier.title;
  }

  if (elements.positioning) {
    elements.positioning.textContent = tier.positioning;
  }

  if (elements.opportunityLevel) {
    elements.opportunityLevel.textContent =
      tier.opportunityLevel;
  }

  if (elements.opportunityText) {
    elements.opportunityText.textContent =
      tier.opportunityText;
  }

  if (elements.analysisLevel) {
    elements.analysisLevel.textContent =
      tier.analysisLevel;
  }

  if (elements.analysisText) {
    elements.analysisText.textContent =
      tier.analysisText;
  }

  if (elements.rankingLevel) {
    elements.rankingLevel.textContent =
      tier.rankingLevel;
  }

  if (elements.rankingText) {
    elements.rankingText.textContent =
      tier.rankingText;
  }

  if (elements.riskLevel) {
    elements.riskLevel.textContent =
      tier.riskLevel;
  }

  if (elements.riskText) {
    elements.riskText.textContent =
      tier.riskText;
  }

  if (elements.benefitsTitle) {
    elements.benefitsTitle.textContent =
      tier.benefitsTitle;
  }


  if (elements.benefits) {

    elements.benefits.innerHTML = "";

    tier.benefits.forEach(function(benefit) {

      const li = document.createElement("li");

      li.textContent = benefit;

      elements.benefits.appendChild(li);

    });

  }


  if (elements.cta) {
    elements.cta.textContent = tier.cta;
  }


  document
    .querySelectorAll("[data-premium-tier]")
    .forEach(function(button) {

      const active =
        button.dataset.premiumTier === tierKey;

      button.classList.toggle("active", active);

      button.setAttribute(
        "aria-selected",
        active ? "true" : "false"
      );

    });

}


function initializePremiumTierSelector() {

  const buttons =
    document.querySelectorAll("[data-premium-tier]");

  if (!buttons.length) {
    return;
  }


  buttons.forEach(function(button) {

    button.addEventListener("click", function() {

      const tierKey =
        button.dataset.premiumTier;

      updatePremiumTier(tierKey);

    });

  });


  updatePremiumTier("starter");

}


document.addEventListener(
  "DOMContentLoaded",
  initializePremiumTierSelector
);