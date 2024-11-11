from contablo.importspec import ImportColumnSpec
from contablo.importspec import ImportMatchRule
from contablo.importspec import ImportSpec

import_spec_dict_acct1_account = ImportSpec(
    label="acct2",
    type="account",
    defaults={"quote_currency": "EUR"},
    columns=[
        ImportColumnSpec(label="Datum", field="tx_date", format="dd.mm.yyyy"),
        ImportColumnSpec(label="Betrag", field="quote_amount+fees", format="0.000,00"),
        ImportColumnSpec(
            label="Verwendungszweck",
            field="note",
            format="",
            match=[
                ImportMatchRule(
                    rule="Kauf WP-Kenn-Nr.: {wkn}, {}, Nominale: {asset_amount}",
                    formats={"asset_amount": "1.000,00"},
                    implies={"tx_type": "BUY"},
                ),
                ImportMatchRule(
                    rule="WP-Kenn-Nr.: {wkn}, {}, Nominale: {asset_amount}",
                    formats={"asset_amount": "1.000,00"},
                    implies={"tx_type": "DIVIDEND", "fees": "0,00/0.000,00"},
                    onlyif={"quote_amount+fees": ">:0,00:number:0.000,00"},
                ),
                ImportMatchRule(rule="bekannt", implies={"tx_type": "DEPOSIT"}, onlyif={}),
            ],
            samples=[],
        ),
        ImportColumnSpec(label="Referenznummer", field="reference"),
    ],
)

import_spec_dict_with_map = ImportSpec(
    label="acct2",
    type="account",
    defaults={"quote_currency": "EUR"},
    columns=[
        ImportColumnSpec(label="Datum", field="tx_date", format="dd.mm.yyyy"),
        ImportColumnSpec(label="Betrag", field="quote_amount+fees", format="0.000,00"),
        ImportColumnSpec(
            label="Richtung",
            field="tx_type",
            format="",
            map={"Kauf": "BUY", "Verkauf": "SELL"},
        ),
        ImportColumnSpec(label="Referenznummer", field="reference"),
    ],
)


import_spec_dict_with_map_and_match = ImportSpec(
    label="acct2",
    type="account",
    defaults={"quote_currency": "EUR"},
    columns=[
        ImportColumnSpec(label="Datum", field="tx_date", format="dd.mm.yyyy"),
        ImportColumnSpec(label="Betrag", field="quote_amount+fees", format="0.000,00"),
        ImportColumnSpec(
            label="Richtung",
            field="tx_type",
            format="",
            map={"Kauf": "BUY", "Verkauf": "SELL"},
            match=[ImportMatchRule(rule="SPLIT", implies={"drop": "drop"})],
        ),
        ImportColumnSpec(label="Referenznummer", field="reference"),
    ],
)


import_spec_inst1_sub1_with_implicit = ImportSpec(
    label="acct1-sub1",
    type="depot",
    defaults={"tx_reference": "acct1-{User_ID}-{Account}-{UTC_Time}"},
    columns=[
        ImportColumnSpec(label="User_ID", field=""),
        ImportColumnSpec(label="UTC_Time", field="tx_datetime", format="yyyy-mm-dd HH:MM:SS"),
        ImportColumnSpec(label="Account", field=""),
        ImportColumnSpec(
            label="Operation",
            field="",
            match=[
                ImportMatchRule(
                    rule="Buy",
                    implies={
                        "tx_type": "SWAP",
                        "asset_amount": "{Change}/1000.00",
                        "asset_currency": "{Coin}",
                        "_allow_add": "yes",
                    },
                    onlyif={"Change": ">:0.00:number:1000.00"},
                ),
                ImportMatchRule(
                    rule="Buy",
                    implies={
                        "tx_type": "SWAP",
                        "quote_amount": "{Change}/1000.00",
                        "quote_currency": "{Coin}",
                        "_allow_add": "yes",
                    },
                    onlyif={"Change": "<:0.00:number:1000.00"},
                ),
                ImportMatchRule(
                    rule="Sell",
                    implies={
                        "tx_type": "SWAP",
                        "asset_amount": "{Change}/1000.00",
                        "asset_currency": "{Coin}",
                        "_allow_add": "yes",
                    },
                    onlyif={"Change": "<:0.00:number:1000.00"},
                ),
                ImportMatchRule(
                    rule="Sell",
                    implies={
                        "tx_type": "SWAP",
                        "quote_amount": "{Change}/1000.00",
                        "quote_currency": "{Coin}",
                        "_allow_add": "yes",
                    },
                    onlyif={"Change": ">:0.00:number:1000.00"},
                ),
                ImportMatchRule(
                    rule="Fee",
                    implies={
                        "fee_amount": "{Change}/1000.00",
                        "fee_currency": "{Coin}",
                        "_allow_add": "yes",
                    },
                ),
                ImportMatchRule(
                    rule="Referral Kickback",
                    implies={
                        "tx_type": "SWAP",
                        "refund_amount": "{Change}/1000.00",
                        "refund_currency": "{Coin}",
                        "_allow_add": "yes",
                    },
                ),
                ImportMatchRule(
                    rule="Referral Commission",
                    implies={
                        "tx_type": "SWAP",
                        "refund_amount": "{Change}/1000.00",
                        "refund_currency": "{Coin}",
                        "_allow_add": "yes",
                    },
                ),
                ImportMatchRule(
                    rule="Inst1 Convert",
                    implies={
                        "tx_type": "SWAP",
                        "asset_amount": "{Change}/1000.00",
                        "asset_currency": "{Coin}",
                        "_allow_add": "yes",
                    },
                    onlyif={"Change": ">:0.00:number:1000.00"},
                ),
                ImportMatchRule(
                    rule="Inst1 Convert",
                    implies={
                        "tx_type": "SWAP",
                        "quote_amount": "{Change}/1000.00",
                        "quote_currency": "{Coin}",
                        "_allow_add": "yes",
                    },
                    onlyif={"Change": "<:0.00:number:1000.00"},
                ),
                ImportMatchRule(
                    rule="Deposit",
                    implies={"tx_type": "DEPOSIT", "quote_amount": "{Change}/1000.00", "quote_currency": "{Coin}"},
                    onlyif={"Change": ">:0.00:number:1000.00"},
                ),
            ],
            samples=[],
        ),
        ImportColumnSpec(label="Coin", field=""),
        ImportColumnSpec(label="Change", field="", format="-1000.00"),
        ImportColumnSpec(label="Remark", field="note"),
    ],
)
