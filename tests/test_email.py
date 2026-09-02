import ssl
import unittest
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import patch

from crypto_digest.email_template import build_subject, render_digest
from crypto_digest.notifier import NotificationManager


def sample_coin(name="Bitcoin", price=67234.125, change=1.25):
    return SimpleNamespace(
        coin_name=name,
        coin_price=price,
        volume_change_24h=change,
        percentage_change_24h=-2.5,
        percentage_change_7d=0.0,
        percentage_change_30d=10.125,
    )


class EmailTemplateTests(unittest.TestCase):
    def setUp(self):
        self.generated_at = datetime(2026, 9, 6, 5, 0, tzinfo=timezone.utc)

    def test_renders_market_data_in_both_formats(self):
        digest = render_digest(
            [sample_coin(), sample_coin("Ethereum", 0.123456, -1.0)],
            generated_at=self.generated_at,
        )

        self.assertIn("#1 Bitcoin — $67,234.12", digest.text_body)
        self.assertIn("#2 Ethereum — $0.1235", digest.text_body)
        self.assertIn("▲ +1.25%", digest.html_body)
        self.assertIn("▼ −2.50%", digest.html_body)
        self.assertIn("— 0.00%", digest.html_body)
        self.assertIn("Top 2 by market capitalization", digest.html_body)
        self.assertLess(digest.html_body.index("Bitcoin"), digest.html_body.index("Ethereum"))

    def test_escapes_dynamic_coin_names(self):
        digest = render_digest(
            [sample_coin("A&B <Coin>")], generated_at=self.generated_at
        )

        self.assertIn("A&amp;B &lt;Coin&gt;", digest.html_body)
        self.assertNotIn("A&B <Coin>", digest.html_body)
        self.assertIn("A&B <Coin>", digest.text_body)

    def test_builds_dated_subject(self):
        self.assertEqual(
            build_subject(self.generated_at),
            "CryptoDigest — Weekly Market Update · Sep 6, 2026",
        )


class NotificationManagerTests(unittest.TestCase):
    @patch("crypto_digest.notifier.SMTP")
    def test_sends_multipart_email_over_tls(self, smtp_class):
        smtp = smtp_class.return_value.__enter__.return_value
        manager = NotificationManager(
            app_email="sender@example.com",
            app_pass="secret",
            personal_email="reader@example.com",
        )

        result = manager.send_email(
            subject="Weekly update",
            text_body="Plain digest",
            html_body="<html><body><strong>HTML digest</strong></body></html>",
        )

        self.assertTrue(result)
        smtp_class.assert_called_once_with(host="smtp.gmail.com")
        smtp.starttls.assert_called_once()
        tls_context = smtp.starttls.call_args.kwargs["context"]
        self.assertEqual(tls_context.minimum_version, ssl.TLSVersion.TLSv1_2)
        self.assertEqual(tls_context.verify_mode, ssl.CERT_REQUIRED)
        self.assertTrue(tls_context.check_hostname)
        smtp.login.assert_called_once_with(
            user="sender@example.com", password="secret"
        )
        smtp.send_message.assert_called_once()

        message = smtp.send_message.call_args.args[0]
        self.assertEqual(message["Subject"], "Weekly update")
        self.assertEqual(message["From"], "CryptoDigest <sender@example.com>")
        self.assertEqual(message["To"], "reader@example.com")
        self.assertTrue(message.is_multipart())
        self.assertIn("Plain digest", message.get_body(preferencelist=("plain",)).get_content())
        self.assertIn("HTML digest", message.get_body(preferencelist=("html",)).get_content())


if __name__ == "__main__":
    unittest.main()
