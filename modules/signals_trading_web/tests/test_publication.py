import json
import tempfile
import unittest
from pathlib import Path

from publisher.public_schema import sanitize_trade
from publisher.validator import validate_data


class PublicationTests(unittest.TestCase):

    def test_private_fields_are_not_published(self):
        row = {
            "ticker": "TEST",
            "entry_price": 10,
            "webull_trade_id": "SECRET",
            "account_number": "PRIVATE"
        }

        result = sanitize_trade(row)

        self.assertNotIn(
            "webull_trade_id",
            result
        )

        self.assertNotIn(
            "account_number",
            result
        )

        self.assertEqual(
            result["ticker"],
            "TEST"
        )

        self.assertEqual(
            result["entry"],
            10
        )

    def test_validator(self):
        with tempfile.TemporaryDirectory() as tmp:
            data_dir = Path(tmp)

            (data_dir / "trades.json").write_text(
                json.dumps(
                    {
                        "generated_at": "",
                        "count": 0,
                        "trades": []
                    }
                ),
                encoding="utf-8"
            )

            (data_dir / "performance.json").write_text(
                json.dumps(
                    {
                        "generated_at": "",
                        "total_trades": 0,
                        "winning_trades": 0,
                        "losing_trades": 0,
                        "win_rate": 0
                    }
                ),
                encoding="utf-8"
            )

            (data_dir / "market.json").write_text(
                json.dumps(
                    {
                        "generated_at": "",
                        "regime": "UNKNOWN"
                    }
                ),
                encoding="utf-8"
            )

            self.assertTrue(
                validate_data(data_dir)
            )


if __name__ == "__main__":
    unittest.main()
