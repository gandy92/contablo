from enum import StrEnum
from enum import auto

from contablo.fields import BoolFieldSpec
from contablo.fields import DateFieldSpec
from contablo.fields import DateTimeFieldSpec
from contablo.fields import DecimalFieldSpec
from contablo.fields import EnumFieldSpec
from contablo.fields import FieldSpec
from contablo.fields import StringFieldSpec
from contablo.fields import TimeFieldSpec
from contablo.importablemerge import LeftRightMatchRule


class FieldID(StrEnum):
    TX_TYPE = auto()
    DEPOT_REF = auto()
    TX_DATE = auto()
    TX_TIME = auto()
    TX_DATETIME = auto()
    TX_REFERENCE = auto()
    REFERENCE = auto()
    ISIN = auto()
    WKN = auto()
    ASSET_AMOUNT = auto()
    ASSET_CURRENCY = auto()
    PRICE_AC = auto()
    EXCHANGE_RATE = auto()
    QUOTE_AMOUNT = auto()
    QUOTE_CURRENCY = auto()
    TAX_AMOUNT = auto()
    FEE_AMOUNT = auto()
    NOTE = auto()


financial_transaction_fields: list[FieldSpec] = [
    StringFieldSpec(FieldID.DEPOT_REF, "Unique number to identify the depot or fiat account."),
    StringFieldSpec(
        "subdepot_ref", "Unique number to identify the subunit of the depot or fiat account or the fnz depot position."
    ),
    EnumFieldSpec(
        FieldID.TX_TYPE,
        "Transaction type",
        [
            "DEPOSIT",
            "WITHDRAW",  # may only make sense if transferred to another account
            "BUY",
            "REINVEST",  # like BUY but initiated by the exchange; suitable for dividend-reinvested or coin staking
            "SELL",
            "SWAP",
            "DIVIDEND",  # asset dividend going to cash account; may be reinvested with optional delay
            "TAX",
            "PRETAX",
            "SPLIT",
        ],
    ),
    DateTimeFieldSpec(FieldID.TX_DATETIME, "Transaction date and time."),
    DateFieldSpec(FieldID.TX_DATE, "Transaction date, to be combined with time"),
    TimeFieldSpec(FieldID.TX_TIME, "Transaction time, to be combined with date"),
    StringFieldSpec(FieldID.TX_REFERENCE, "Order reference, defaults to reference, then new uuid"),
    DateTimeFieldSpec("order_datetime", "Order date and time."),
    DateFieldSpec("order_date", "Order date, to be combined with time"),
    TimeFieldSpec("order_time", "Order time, to be combined with date"),
    StringFieldSpec("order_reference", "Order reference, defaults to reference."),
    # Todo: Which fields are required to carry snapshot information?
    DateTimeFieldSpec("snapshot_datetime", "Transaction date and time."),
    DateFieldSpec("snapshot_date", "Transaction date, to be combined with time"),
    TimeFieldSpec("snapshot_time", "Transaction time, to be combined with date"),
    # Asset related
    StringFieldSpec(FieldID.ISIN, "Asset ISIN code, if applicable."),
    StringFieldSpec(FieldID.WKN, "Asset WKN code, if applicable."),
    DecimalFieldSpec(FieldID.ASSET_AMOUNT, "Amount of added or removed asset units."),
    StringFieldSpec("asset_symbol", "Asset ticker symbol, e.g. onvista home symbol."),
    StringFieldSpec(FieldID.ASSET_CURRENCY, "Base currency of the asset price."),
    StringFieldSpec("asset_type", "Type of Asset."),
    DecimalFieldSpec(FieldID.PRICE_AC, "Price in terms of asset currency/asset unit."),
    DecimalFieldSpec("price", "Price in terms of quote currency/asset unit."),
    DecimalFieldSpec(FieldID.EXCHANGE_RATE, "Price in terms of quote currency/asset currency."),
    DecimalFieldSpec(FieldID.QUOTE_AMOUNT, "Amount in quote currency."),
    StringFieldSpec(
        FieldID.QUOTE_CURRENCY, "Currency in which the asset is quoted, e.g. USD or EUR, or a asset_symbol."
    ),
    DecimalFieldSpec(FieldID.FEE_AMOUNT, "Fees payed in quote currency."),
    StringFieldSpec("fee_currency", "Currency in which the fees are paid, defaults to quote_currency."),
    DecimalFieldSpec("refund_amount", "Fees payed in quote currency."),
    StringFieldSpec("refund_currency", "Currency in which the fees are paid, defaults to quote_currency."),
    DecimalFieldSpec(FieldID.TAX_AMOUNT, "Redacted taxes in addition to what is included in the value."),
    StringFieldSpec("tax_currency", "Currency in which the taxes are paid, defaults to quote_currency."),
    DecimalFieldSpec("quote_amount+fees", "Sum of quote_amount and fees, requires additional information."),
    DecimalFieldSpec("quote_amount+taxes", "Sum of quote_amount and redacted taxes, unclear how to handle this."),
    StringFieldSpec(FieldID.REFERENCE, "Unspecific reference, may be matched to a more specific one."),
    StringFieldSpec("stock_exchange", "Where a certain stock was bought."),
    StringFieldSpec(FieldID.NOTE, "Transaction motes."),
    # flags for internal operations like merging:
    BoolFieldSpec("_allow_add", "Indicates that amounts with the same tx_reference may be added"),
]

# rules on how to match certain fields when merging two aspects of the same event
# (coming from two different file configurations) are merged:
match_rules = [
    LeftRightMatchRule({"tx_reference": "tx_reference"}, ["imported_from"]),
    LeftRightMatchRule({"order_reference": "order_reference"}, ["imported_from"]),
    LeftRightMatchRule({"reference": "reference"}, ["imported_from"]),
    LeftRightMatchRule({"order_reference": "reference"}, ["imported_from"]),
    LeftRightMatchRule({"reference": "order_reference"}, ["imported_from"]),
]
# fields to be ignored if _allow_add is True:
addable_fields = ["asset_amount", "quote_amount"]
