"""
====================================================================
NEA28 SEC XBRL CONCEPT REGISTRY

Module:
    sec_concepts.py

Purpose:
    Central SEC XBRL concept definitions used by all SEC analysis
    plugins.

Design:
    - Single source of truth for SEC concepts
    - Plugin independent
    - Supports alternate SEC XBRL reporting concepts
    - Used by SECAnalysisExtensions
====================================================================
"""

SEC_COLUMNS = [
    "concept",
    "label",
    "value",
    "numeric_value",
    "unit",
    "period_type",
    "period_start",
    "period_end",
    "fiscal_year",
    "fiscal_period",
]

SEC_DEI_CONCEPTS = {
    "PUBLIC_FLOAT": [
        "dei:EntityPublicFloat",
    ],
    "SHARES_OUTSTANDING": [
        "dei:EntityCommonStockSharesOutstanding",
    ],
}

SEC_EARNINGS_CONCEPTS = {
    "NET_INCOME": [
        "us-gaap:NetIncomeLoss",
        "us-gaap:ProfitLoss",
        "us-gaap:NetIncomeLossAvailableToCommonStockholdersBasic",
        "us-gaap:IncomeLossFromContinuingOperations",
    ],
    "EPS_BASIC": [
        "us-gaap:EarningsPerShareBasic",
    ],
    "EPS_DILUTED": [
        "us-gaap:EarningsPerShareDiluted",
    ],
    "WEIGHTED_SHARES_BASIC": [
        "us-gaap:WeightedAverageNumberOfSharesOutstandingBasic",
    ],
    "WEIGHTED_SHARES_DILUTED": [
        "us-gaap:WeightedAverageNumberOfDilutedSharesOutstanding",
    ],
}

SEC_INCOME_CONCEPTS = {
    "REVENUE": [
        "us-gaap:Revenues",
        "us-gaap:SalesRevenueNet",
        "us-gaap:SalesRevenueGoodsNet",
        "us-gaap:SalesRevenueServicesNet",
        "us-gaap:RevenueFromContractWithCustomerExcludingAssessedTax",
    ],
    "OPERATING_INCOME": [
        "us-gaap:OperatingIncomeLoss",
        "us-gaap:IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest",
    ],
    "GROSS_PROFIT": [
        "us-gaap:GrossProfit",
    ],
    "COST_OF_GOODS_SOLD": [
        "us-gaap:CostOfGoodsAndServicesSold",
    ],
    "NET_INCOME": [
        "us-gaap:NetIncomeLoss",
    ],
    "PROFIT_LOSS": [
        "us-gaap:ProfitLoss",
    ],
    "NET_INCOME_COMMON": [
        "us-gaap:NetIncomeLossAvailableToCommonStockholdersBasic",
    ],
    "CONTINUING_OPERATIONS": [
        "us-gaap:IncomeLossFromContinuingOperations",
    ],
    "EPS_BASIC": [
        "us-gaap:EarningsPerShareBasic",
    ],
    "EPS_DILUTED": [
        "us-gaap:EarningsPerShareDiluted",
    ],
    "WEIGHTED_SHARES_BASIC": [
        "us-gaap:WeightedAverageNumberOfSharesOutstandingBasic",
    ],
    "WEIGHTED_SHARES_DILUTED": [
        "us-gaap:WeightedAverageNumberOfDilutedSharesOutstanding",
    ],
    "R_AND_D": [
        "us-gaap:ResearchAndDevelopmentExpense",
    ],
    "SGA": [
        "us-gaap:SellingGeneralAndAdministrativeExpense",
    ],
    "SALES_MARKETING": [
        "us-gaap:SellingAndMarketingExpense",
    ],
    "GENERAL_ADMIN": [
        "us-gaap:GeneralAndAdministrativeExpense",
    ],
    "INCOME_TAX": [
        "us-gaap:IncomeTaxExpenseBenefit",
    ],
    "NON_OPERATING": [
        "us-gaap:NonoperatingIncomeExpense",
    ],
    "INTEREST_EXPENSE": [
        "us-gaap:InterestExpense",
    ],
    "INTEREST_COSTS": [
        "us-gaap:InterestCostsIncurred",
    ],
    "COMPREHENSIVE_INCOME": [
        "us-gaap:ComprehensiveIncome",
    ],
    "FINANCE_COSTS": [
        "us-gaap:FinanceCosts",
    ],
    "OTHER_GA_EXPENSE": [
        "us-gaap:OtherGeneralAndAdministrativeExpense",
    ],
    "OTHER_NONOPERATING": [
        "us-gaap:OtherNonoperatingIncomeExpense",
    ],
    "FOREIGN_EXCHANGE_LOSS": [
        "us-gaap:ForeignExchangeLoss",
    ],
    "FOREIGN_CURRENCY_GAIN_LOSS": [
        "us-gaap:ForeignCurrencyTransactionGainLossBeforeTax",
    ],
    "EXCHANGE_TRANSLATION_GAIN_LOSS": [
        "us-gaap:GainsLossesOnExchangeDifferencesOnTranslationNetOfTax",
    ],
    "DEBT_EXTINGUISHMENT_GAIN_LOSS": [
        "us-gaap:GainsLossesOnExtinguishmentOfDebt",
    ],
    "INVESTMENT_INTEREST_INCOME": [
        "us-gaap:InvestmentIncomeInterest",
    ],
    "LABOR_EXPENSE": [
        "us-gaap:LaborAndRelatedExpense",
    ],
    "REVENUES": [
        "us-gaap:Revenues",
    ],
    "NET_INCOME_NONCONTROLLING": [
        "us-gaap:NetIncomeLossIncludingPortionAttributableToNonredeemableNoncontrollingInterest",
    ],
    "ADJUSTMENT_FOR_AMORTIZATION": [
        "us-gaap:AdjustmentForAmortization",
    ],
    "DEPRECIATION_AND_AMORTIZATION": [
        "us-gaap:DepreciationAndAmortization",
    ],
    "INTEREST_PAID": [
        "us-gaap:InterestPaid",
    ],
    "PROFESSIONAL_FEES": [
        "us-gaap:ProfessionalFees",
    ],
}

SEC_BALANCE_SHEET_CONCEPTS = {
    "TOTAL_ASSETS": [
        "us-gaap:Assets",
    ],
    "CURRENT_ASSETS": [
        "us-gaap:AssetsCurrent",
    ],
    "NONCURRENT_ASSETS": [
        "us-gaap:AssetsNoncurrent",
    ],
    "CASH": [
        "us-gaap:CashAndCashEquivalentsAtCarryingValue",
    ],
    "CASH_RESTRICTED": [
        "us-gaap:CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents",
    ],
    "ACCOUNTS_RECEIVABLE": [
        "us-gaap:AccountsReceivableNetCurrent",
    ],
    "INVENTORY": [
        "us-gaap:InventoryNet",
    ],
    "PPE_NET": [
        "us-gaap:PropertyPlantAndEquipmentNet",
    ],
    "PPE_GROSS": [
        "us-gaap:PropertyPlantAndEquipmentGross",
    ],
    "ACCUMULATED_DEPRECIATION": [
        "us-gaap:AccumulatedDepreciationDepletionAndAmortizationPropertyPlantAndEquipment",
    ],
    "INTANGIBLE_ASSETS": [
        "us-gaap:IntangibleAssetsNetExcludingGoodwill",
    ],
    "INTANGIBLE_ASSETS_GROSS": [
        "us-gaap:IntangibleAssetsGrossExcludingGoodwill",
    ],
    "TOTAL_LIABILITIES": [
        "us-gaap:Liabilities",
    ],
    "CURRENT_LIABILITIES": [
        "us-gaap:LiabilitiesCurrent",
    ],
    "NONCURRENT_LIABILITIES": [
        "us-gaap:LiabilitiesNoncurrent",
    ],
    "ACCOUNTS_PAYABLE": [
        "us-gaap:AccountsPayableCurrent",
    ],
    "STOCKHOLDERS_EQUITY": [
        "us-gaap:StockholdersEquity",
    ],
    "RETAINED_EARNINGS": [
        "us-gaap:RetainedEarningsAccumulatedDeficit",
    ],
    "MARKETABLE_SECURITIES_CURRENT": [
        "us-gaap:MarketableSecuritiesCurrent",
    ],
    "MARKETABLE_SECURITIES_NONCURRENT": [
        "us-gaap:MarketableSecuritiesNoncurrent",
    ],
    "OTHER_ASSETS_CURRENT": [
        "us-gaap:OtherAssetsCurrent",
    ],
    "OTHER_ASSETS_NONCURRENT": [
        "us-gaap:OtherAssetsNoncurrent",
    ],
    "OTHER_LIABILITIES_CURRENT": [
        "us-gaap:OtherLiabilitiesCurrent",
    ],
    "OTHER_LIABILITIES_NONCURRENT": [
        "us-gaap:OtherLiabilitiesNoncurrent",
    ],
    "ACCOUNTS_RECEIVABLE_GROSS": [
        "us-gaap:AccountsReceivableGross",
    ],
    "ACCOUNTS_RECEIVABLE_NET": [
        "us-gaap:AccountsReceivableNet",
    ],
    "ADDITIONAL_PAID_IN_CAPITAL": [
        "us-gaap:AdditionalPaidInCapital",
    ],
    "DEFERRED_REVENUE": [
        "us-gaap:DeferredRevenue",
    ],
    "MARKETABLE_SECURITIES": [
        "us-gaap:MarketableSecurities",
    ],
    "GOODWILL_IMPAIRMENT": [
        "us-gaap:GoodwillImpairmentLoss",
    ],
    "PREPAID_EXPENSE_NONCURRENT": [
        "us-gaap:PrepaidExpenseNoncurrent",
    ],
    "LIABILITIES_AND_EQUITY": [
        "us-gaap:LiabilitiesAndStockholdersEquity",
    ],
    "STOCKHOLDERS_EQUITY_NONCONTROLLING": [
        "us-gaap:StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest",
    ],
    "OTHER_EQUITY_INTEREST": [
        "us-gaap:OtherEquityInterest",
    ],
    "OTHER_RESERVES": [
        "us-gaap:OtherReserves",
    ],
    "RIGHT_OF_USE_ASSETS": [
        "us-gaap:RightofuseAssets",
    ],
    "GOODWILL": [
        "us-gaap:Goodwill",
    ],
}

SEC_SHARE_CONCEPTS = {
    "COMMON_SHARES_OUTSTANDING": [
        "us-gaap:CommonStockSharesOutstanding",
    ],
    "SHARES_ISSUED": [
        "us-gaap:CommonStockSharesIssued",
    ],
    "SHARES_AUTHORIZED": [
        "us-gaap:CommonStockSharesAuthorized",
    ],
    "WEIGHTED_BASIC": [
        "us-gaap:WeightedAverageNumberOfSharesOutstandingBasic",
    ],
    "WEIGHTED_DILUTED": [
        "us-gaap:WeightedAverageNumberOfDilutedSharesOutstanding",
    ],
    "SHARE_BASED_COMPENSATION": [
        "us-gaap:ShareBasedCompensation",
    ],
    "ALLOCATED_SHARE_COMPENSATION": [
        "us-gaap:AllocatedShareBasedCompensationExpense",
    ],
    "INCREMENTAL_SHARES": [
        "us-gaap:IncrementalCommonSharesAttributableToShareBasedPaymentArrangements",
    ],
    "REPURCHASED_SHARES": [
        "us-gaap:StockRepurchasedAndRetiredDuringPeriodShares",
    ],
    "REPURCHASED_VALUE": [
        "us-gaap:StockRepurchasedAndRetiredDuringPeriodValue",
    ],
    "CAPITAL_UNITS_AUTHORIZED": [
        "us-gaap:CapitalUnitsAuthorized",
    ],
    "CAPITAL_UNITS_OUTSTANDING": [
        "us-gaap:CapitalUnitsOutstanding",
    ],
    "COMMON_STOCK_VALUE": [
        "us-gaap:CommonStockValue",
    ],
    "COMMON_STOCK_PAR_VALUE": [
        "us-gaap:CommonStockParOrStatedValuePerShare",
    ],
    "PREFERRED_STOCK_VALUE": [
        "us-gaap:PreferredStockValue",
    ],
    "PREFERRED_STOCK_SHARES_OUTSTANDING": [
        "us-gaap:PreferredStockSharesOutstanding",
    ],
    "PREFERRED_STOCK_SHARES_AUTHORIZED": [
        "us-gaap:PreferredStockSharesAuthorized",
    ],
    "PREFERRED_STOCK_CONVERTIBLE_SHARES": [
        "us-gaap:PreferredStockConvertibleSharesIssuable",
    ],
    "STOCK_GRANTED_SHARE_BASED_COMP": [
        "us-gaap:StockGrantedDuringPeriodValueSharebasedCompensation",
    ],
    "EMPLOYEE_SHARE_BASED_COMP_NONCASH": [
        "us-gaap:EmployeeBenefitsAndShareBasedCompensationNoncash",
    ],
    "STOCK_AND_WARRANTS_ISSUED": [
        "us-gaap:IssuanceOfStockAndWarrantsForServicesOrClaims",
    ],
    "WARRANTS_OUTSTANDING": [
        "us-gaap:WarrantsAndRightsOutstanding",
    ],
    "WARRANT_CLASS_OUTSTANDING": [
        "us-gaap:ClassOfWarrantOrRightOutstanding",
    ],
    "SUBSCRIPTIONS_RECEIVABLE": [
        "us-gaap:StockholdersEquityNoteSubscriptionsReceivable",
    ],
    "RECEIVABLE_FROM_SHAREHOLDERS": [
        "us-gaap:ReceivableFromShareholdersOrAffiliatesForIssuanceOfCapitalStock",
    ],
    "TREASURY_STOCK_SHARES": [
        "us-gaap:TreasuryStockShares",
    ],
    "TREASURY_STOCK_VALUE": [
        "us-gaap:TreasuryStockValue",
    ],
    "TREASURY_STOCK_COST": [
        "us-gaap:TreasuryStockValueAcquiredCostMethod",
    ],
    "TREASURY_STOCK_ACQUIRED": [
        "us-gaap:TreasuryStockAcquiredDuringPeriodShares",
    ],
    "TREASURY_STOCK_REISSUED": [
        "us-gaap:TreasuryStockReissuedDuringPeriodShares",
    ],
    "TREASURY_STOCK_RETIRED": [
        "us-gaap:TreasuryStockRetiredDuringPeriodShares",
    ],
    "TREASURY_STOCK_ACQUIRED_VALUE": [
        "us-gaap:TreasuryStockAcquiredDuringPeriodValue",
    ],
    "TREASURY_STOCK_REISSUED_VALUE": [
        "us-gaap:TreasuryStockReissuedDuringPeriodValue",
    ],
    "TREASURY_STOCK_RETIRED_VALUE": [
        "us-gaap:TreasuryStockRetiredDuringPeriodValue",
    ],
}

SEC_TREASURY_STOCK_CONCEPTS = {
    "TREASURY_SHARES": [
        "TreasuryStockShares",
        "TreasuryShares",
        "CommonStockTreasuryShares",
        "TreasuryStockCommonShares",
        "TreasuryStockSharesHeld",
        "TreasuryStockHeld",
    ],
    "TREASURY_VALUE": [
        "TreasuryStockValue",
        "TreasuryStockAmount",
        "TreasuryStockCarryingAmount",
        "TreasuryStockBalance",
        "TreasuryStock",
    ],
    "TREASURY_COST": [
        "TreasuryStockCost",
        "TreasuryStockAcquisitionCost",
        "TreasuryStockAtCost",
        "TreasuryStockCostMethodAmount",
    ],
}

SEC_CASHFLOW_CONCEPTS = {
    "OPERATING_CASHFLOW": [
        "us-gaap:NetCashProvidedByUsedInOperatingActivities",
    ],
    "INVESTING_CASHFLOW": [
        "us-gaap:NetCashProvidedByUsedInInvestingActivities",
    ],
    "FINANCING_CASHFLOW": [
        "us-gaap:NetCashProvidedByUsedInFinancingActivities",
    ],
    "CAPEX": [
        "us-gaap:PaymentsToAcquirePropertyPlantAndEquipment",
    ],
    "DIVIDENDS": [
        "us-gaap:PaymentsOfDividends",
    ],
    "SHARE_REPURCHASES": [
        "us-gaap:PaymentsForRepurchaseOfCommonStock",
    ],
    "DEBT_ISSUED": [
        "us-gaap:ProceedsFromIssuanceOfLongTermDebt",
    ],
    "DEBT_REPAID": [
        "us-gaap:RepaymentsOfLongTermDebt",
    ],
    "SECURITIES_PURCHASED": [
        "us-gaap:PaymentsToAcquireAvailableForSaleSecuritiesDebt",
    ],
    "SECURITIES_SOLD": [
        "us-gaap:ProceedsFromSaleOfAvailableForSaleSecuritiesDebt",
    ],
    "DEPRECIATION": [
        "us-gaap:Depreciation",
    ],
    "DEPRECIATION_AMORTIZATION": [
        "us-gaap:DepreciationDepletionAndAmortization",
    ],
    "CHANGE_ACCOUNTS_RECEIVABLE": [
        "us-gaap:IncreaseDecreaseInAccountsReceivable",
    ],
    "CHANGE_ACCOUNTS_PAYABLE": [
        "us-gaap:IncreaseDecreaseInAccountsPayable",
    ],
    "CHANGE_INVENTORY": [
        "us-gaap:IncreaseDecreaseInInventories",
    ],
    "OTHER_OPERATING_ASSETS": [
        "us-gaap:IncreaseDecreaseInOtherOperatingAssets",
    ],
    "OTHER_OPERATING_LIABILITIES": [
        "us-gaap:IncreaseDecreaseInOtherOperatingLiabilities",
    ],
    "EFFECT_OF_EXCHANGE_RATE_ON_CASH": [
        "us-gaap:EffectOfExchangeRateOnCashCashEquivalentsRestrictedCashAndRestrictedCashEquivalentsIncludingDisposalGroupAndDiscontinuedOperations",
    ],
    "PAYMENTS_FOR_PROCEEDS_FROM_BUSINESSES_AND_INTEREST_IN_AFFILIATES": [
        "us-gaap:PaymentsForProceedsFromBusinessesAndInterestInAffiliates",
    ],
    "PAYMENTS_FOR_PROCEEDS_FROM_INVESTMENTS": [
        "us-gaap:PaymentsForProceedsFromInvestments",
    ],
    "PAYMENTS_FOR_PROCEEDS_FROM_LOANS_RECEIVABLE": [
        "us-gaap:PaymentsForProceedsFromLoansReceivable",
    ],
    "PAYMENTS_TO_ACQUIRE_OTHER_PRODUCTIVE_ASSETS": [
        "us-gaap:PaymentsToAcquireOtherProductiveAssets",
    ],
    "PROCEEDS_FROM_CONVERTIBLE_DEBT": [
        "us-gaap:ProceedsFromConvertibleDebt",
    ],
    "PROCEEDS_FROM_DEBT_NET_OF_ISSUANCE_COSTS": [
        "us-gaap:ProceedsFromDebtNetOfIssuanceCosts",
    ],
    "PROCEEDS_FROM_ISSUANCE_OF_COMMON_STOCK": [
        "us-gaap:ProceedsFromIssuanceOfCommonStock",
    ],
    "PROCEEDS_FROM_REPAYMENTS_OF_LINES_OF_CREDIT": [
        "us-gaap:ProceedsFromRepaymentsOfLinesOfCredit",
    ],
    "PROCEEDS_FROM_SALES_OF_ASSETS_INVESTING_ACTIVITIES": [
        "us-gaap:ProceedsFromSalesOfAssetsInvestingActivities",
    ],
    "PROCEEDS_FROM_WARRANT_EXERCISES": [
        "us-gaap:ProceedsFromWarrantExercises",
    ],
    "REPAYMENTS_OF_OTHER_DEBT": [
        "us-gaap:RepaymentsOfOtherDebt",
    ],
}

SEC_DEBT_CONCEPTS = {
    "LONG_TERM_DEBT": [
        "us-gaap:LongTermDebt",
    ],
    "LONG_TERM_DEBT_CURRENT": [
        "us-gaap:LongTermDebtCurrent",
    ],
    "LONG_TERM_DEBT_NONCURRENT": [
        "us-gaap:LongTermDebtNoncurrent",
    ],
    "DEBT_CARRYING_VALUE": [
        "us-gaap:DebtInstrumentCarryingAmount",
    ],
    "DEBT_UNAMORTIZED_COST": [
        "us-gaap:DebtInstrumentUnamortizedDiscountPremiumAndDebtIssuanceCostsNet",
    ],
    "COMMERCIAL_PAPER": [
        "us-gaap:CommercialPaper",
    ],
    "DEBT_REPAYMENT_CURRENT": [
        "us-gaap:LongTermDebtMaturitiesRepaymentsOfPrincipalInNextTwelveMonths",
    ],
    "LINE_OF_CREDIT": [
        "us-gaap:LineOfCredit",
    ],
    "LOANS_PAYABLE": [
        "us-gaap:LoansPayable",
    ],
    "CONVERTIBLE_DEBT": [
        "us-gaap:ConvertibleDebt",
    ],
    "LONG_TERM_DEBT_CAPITAL_LEASE": [
        "us-gaap:LongTermDebtAndCapitalLeaseObligations",
    ],
}

SEC_TAX_CONCEPTS = {
    "INCOME_TAX": [
        "us-gaap:IncomeTaxExpenseBenefit",
    ],
    "INCOME_TAX_PAID": [
        "us-gaap:IncomeTaxesPaidNet",
    ],
    "EFFECTIVE_TAX_RATE": [
        "us-gaap:EffectiveIncomeTaxRateContinuingOperations",
    ],
    "DEFERRED_TAX_ASSETS": [
        "us-gaap:DeferredTaxAssetsNet",
    ],
    "DEFERRED_TAX_LIABILITIES": [
        "us-gaap:DeferredIncomeTaxLiabilities",
    ],
    "TAX_ASSET_GROSS": [
        "us-gaap:DeferredTaxAssetsGross",
    ],
    "TAX_VALUATION_ALLOWANCE": [
        "us-gaap:DeferredTaxAssetsValuationAllowance",
    ],
    "DEFERRED_TAXES_AND_CREDITS": [
        "us-gaap:DeferredIncomeTaxesAndTaxCredits",
    ],
}

SEC_LEASE_CONCEPTS = {
    "FINANCE_LEASE_LIABILITY": [
        "us-gaap:FinanceLeaseLiability",
    ],
    "FINANCE_LEASE_CURRENT": [
        "us-gaap:FinanceLeaseLiabilityCurrent",
    ],
    "FINANCE_LEASE_NONCURRENT": [
        "us-gaap:FinanceLeaseLiabilityNoncurrent",
    ],
    "FINANCE_LEASE_ASSET": [
        "us-gaap:FinanceLeaseRightOfUseAsset",
    ],
    "OPERATING_LEASE_LIABILITY": [
        "us-gaap:OperatingLeaseLiability",
    ],
    "OPERATING_LEASE_CURRENT": [
        "us-gaap:OperatingLeaseLiabilityCurrent",
    ],
    "OPERATING_LEASE_NONCURRENT": [
        "us-gaap:OperatingLeaseLiabilityNoncurrent",
    ],
    "OPERATING_LEASE_ASSET": [
        "us-gaap:OperatingLeaseRightOfUseAsset",
    ],
    "VARIABLE_LEASE_PAYMENT": [
        "us-gaap:VariableLeasePayment",
    ],
}

SEC_INVESTMENT_CONCEPTS = {
    "AVAILABLE_FOR_SALE_SECURITIES": [
        "us-gaap:AvailableForSaleSecuritiesDebtMaturitiesSingleMaturityDate",
    ],
    "SECURITIES_CURRENT": [
        "us-gaap:MarketableSecuritiesCurrent",
    ],
    "SECURITIES_NONCURRENT": [
        "us-gaap:MarketableSecuritiesNoncurrent",
    ],
    "UNREALIZED_GAIN_LOSS_INVESTMENTS": [
        "us-gaap:UnrealizedGainLossOnInvestments",
    ],
}

SEC_ADDITIONAL_CONCEPTS = {
    "ACCOUNTS_FINANCING_RECEIVABLE_ALLOWANCE": [
        "us-gaap:AccountsAndFinancingReceivableAllowanceForCreditLoss",
    ],
    "ACCOUNTS_PAYABLE_ACCRUED_CURRENT": [
        "us-gaap:AccountsPayableAndAccruedLiabilitiesCurrent",
    ],
    "ACCRETION_EXPENSE": [
        "us-gaap:AccretionExpense",
    ],
    "ADJUSTMENTS_UNREALIZED_FX": [
        "us-gaap:AdjustmentsForUnrealisedForeignExchangeLossesGains",
    ],
    "ADVANCES": [
        "us-gaap:Advances",
    ],
    "ADVANCES_TO_AFFILIATE": [
        "us-gaap:AdvancesToAffiliate",
    ],
    "CASH_CHANGE_RESTRICTED_EXCHANGE_EFFECT": [
        "us-gaap:CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalentsPeriodIncreaseDecreaseIncludingExchangeRateEffect",
    ],
    "COMMUNICATIONS_INFORMATION_TECHNOLOGY": [
        "us-gaap:CommunicationsAndInformationTechnology",
    ],
    "DERIVATIVE_LIABILITIES": [
        "us-gaap:DerivativeLiabilities",
    ],
    "FINITE_LIVED_INTANGIBLE_ASSETS": [
        "us-gaap:FiniteLivedIntangibleAssetsNet",
    ],
    "CHANGE_ACCOUNTS_PAYABLE_ACCRUED": [
        "us-gaap:IncreaseDecreaseInAccountsPayableAndAccruedLiabilities",
    ],
    "CHANGE_INVENTORY_LONG_TERM": [
        "us-gaap:IncreaseDecreaseInInventoryForLongTermContractsOrPrograms",
    ],
    "CHANGE_MARKETABLE_SECURITIES_RESTRICTED": [
        "us-gaap:IncreaseDecreaseInMarketableSecuritiesRestricted",
    ],
    "CHANGE_NOTES_RECEIVABLE_RELATED_PARTIES": [
        "us-gaap:IncreaseDecreaseInNotesReceivableRelatedPartiesCurrent",
    ],
    "CHANGE_OTHER_ACCRUED_LIABILITIES": [
        "us-gaap:IncreaseDecreaseInOtherAccruedLiabilities",
    ],
    "CHANGE_OTHER_RECEIVABLES": [
        "us-gaap:IncreaseDecreaseInOtherReceivables",
    ],
    "INSURANCE_FINANCE_INCOME_EXPENSE": [
        "us-gaap:InsuranceFinanceIncomeExpenses",
    ],
    "NOTES_AND_LOANS_RECEIVABLE_NONCURRENT": [
        "us-gaap:NotesAndLoansReceivableNetNoncurrent",
    ],
    "NOTES_RECEIVABLE": [
        "us-gaap:NotesReceivableNet",
    ],
    "OTHER_SIGNIFICANT_NONCASH_CONSIDERATION": [
        "us-gaap:OtherSignificantNoncashTransactionValueOfConsiderationReceived1",
    ],
    "PROVISION_LOAN_LOSSES": [
        "us-gaap:ProvisionForLoanLeaseAndOtherLosses",
    ],
    "RECOGNITION_OF_DEFERRED_REVENUE": [
        "us-gaap:RecognitionOfDeferredRevenue",
    ],
}

SEC_REGISTRIES = {
    "DEI": SEC_DEI_CONCEPTS,
    "EARNINGS": SEC_EARNINGS_CONCEPTS,
    "INCOME": SEC_INCOME_CONCEPTS,
    "BALANCE_SHEET": SEC_BALANCE_SHEET_CONCEPTS,
    "SHARE": SEC_SHARE_CONCEPTS,
    "CASHFLOW": SEC_CASHFLOW_CONCEPTS,
    "DEBT": SEC_DEBT_CONCEPTS,
    "TAX": SEC_TAX_CONCEPTS,
    "LEASE": SEC_LEASE_CONCEPTS,
    "INVESTMENT": SEC_INVESTMENT_CONCEPTS,
    "ADDITIONAL": SEC_ADDITIONAL_CONCEPTS,
    "TREASURY_STOCK": SEC_TREASURY_STOCK_CONCEPTS,
}