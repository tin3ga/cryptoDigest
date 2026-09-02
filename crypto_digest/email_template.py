"""Render the weekly cryptocurrency digest as email-safe content."""

from dataclasses import dataclass
from datetime import datetime, timezone
from html import escape
from typing import Iterable, Optional, Protocol


class CoinLike(Protocol):
    """The market fields required by the email template."""

    coin_name: str
    coin_price: float
    volume_change_24h: float
    percentage_change_24h: float
    percentage_change_7d: float
    percentage_change_30d: float


@dataclass(frozen=True)
class DigestContent:
    """The two representations included in a multipart email."""

    text_body: str
    html_body: str


def _format_date(value: datetime, abbreviated: bool = False) -> str:
    month = value.strftime("%b" if abbreviated else "%B")
    return f"{month} {value.day}, {value.year}"


def _format_price(value: float) -> str:
    absolute_value = abs(value)
    if absolute_value >= 1:
        return f"${value:,.2f}"
    if absolute_value >= 0.01:
        return f"${value:,.4f}"
    return f"${value:,.8f}"


def _format_change(value: float) -> str:
    if value > 0:
        return f"▲ +{value:.2f}%"
    if value < 0:
        return f"▼ −{abs(value):.2f}%"
    return "— 0.00%"


def _change_color(value: float) -> str:
    if value > 0:
        return "#42d392"
    if value < 0:
        return "#ff6b81"
    return "#aab4cc"


def build_subject(generated_at: datetime) -> str:
    """Build the dated subject line for a weekly digest."""

    return f"CryptoDigest — Weekly Market Update · {_format_date(generated_at, abbreviated=True)}"


def render_digest(
    coins: Iterable[CoinLike], generated_at: Optional[datetime] = None
) -> DigestContent:
    """Render coin market data into plain-text and HTML email bodies."""

    generated_at = generated_at or datetime.now(timezone.utc)
    coin_list = list(coins)
    report_date = _format_date(generated_at)

    text_lines = [
        "CRYPTODIGEST",
        "Weekly Market Update",
        f"Top cryptocurrencies at a glance · {report_date} UTC",
        "",
    ]
    html_rows = []

    for rank, coin in enumerate(coin_list, start=1):
        changes = (
            ("24H VOLUME", coin.volume_change_24h),
            ("24H PRICE", coin.percentage_change_24h),
            ("7D PRICE", coin.percentage_change_7d),
            ("30D PRICE", coin.percentage_change_30d),
        )

        text_lines.extend(
            [
                f"#{rank} {coin.coin_name} — {_format_price(coin.coin_price)}",
                "  " + " | ".join(
                    f"{label.title()}: {_format_change(value)}"
                    for label, value in changes
                ),
                "",
            ]
        )

        metric_cells = "".join(
            f"""
            <td class="metric" width="25%" style="padding: 14px 8px 4px; text-align: center; vertical-align: top;">
              <div style="color: #7f8aa5; font-size: 10px; font-weight: 700; letter-spacing: 0.8px; line-height: 14px;">{label}</div>
              <div style="color: {_change_color(value)}; font-size: 14px; font-weight: 700; line-height: 22px; white-space: nowrap;">{_format_change(value)}</div>
            </td>"""
            for label, value in changes
        )

        html_rows.append(
            f"""
          <tr>
            <td style="padding: 0 24px 14px;">
              <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="background: #151d33; border: 1px solid #26314f; border-radius: 12px;">
                <tr>
                  <td style="padding: 18px 18px 8px;">
                    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0">
                      <tr>
                        <td style="vertical-align: middle;">
                          <span style="display: inline-block; min-width: 26px; padding: 5px 3px; border-radius: 7px; background: #212c49; color: #8ea0c9; font-size: 11px; font-weight: 700; text-align: center; vertical-align: middle;">#{rank}</span>
                          <span style="padding-left: 10px; color: #f5f7ff; font-size: 18px; font-weight: 700; vertical-align: middle;">{escape(coin.coin_name)}</span>
                        </td>
                        <td style="color: #f5f7ff; font-size: 18px; font-weight: 700; text-align: right; vertical-align: middle; white-space: nowrap;">{_format_price(coin.coin_price)}</td>
                      </tr>
                    </table>
                  </td>
                </tr>
                <tr>
                  <td style="padding: 0 10px 14px;">
                    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0">
                      <tr>{metric_cells}
                      </tr>
                    </table>
                  </td>
                </tr>
              </table>
            </td>
          </tr>"""
        )

    text_lines.extend(
        [
            "Market data is informational and is not financial advice.",
            "Delivered weekly by CryptoDigest.",
        ]
    )

    coin_count = len(coin_list)
    preheader = f"Your weekly snapshot of the top {coin_count} cryptocurrencies."
    html_body = f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <meta name="color-scheme" content="dark">
    <meta name="supported-color-schemes" content="dark">
    <title>CryptoDigest Weekly Market Update</title>
    <style>
      @media only screen and (max-width: 620px) {{
        .email-shell {{ width: 100% !important; }}
        .email-padding {{ padding-left: 16px !important; padding-right: 16px !important; }}
        .metric {{ display: inline-block !important; width: 50% !important; box-sizing: border-box !important; }}
      }}
    </style>
  </head>
  <body style="margin: 0; padding: 0; background: #090e1a; color: #f5f7ff; font-family: Arial, Helvetica, sans-serif;">
    <div style="display: none; max-height: 0; overflow: hidden; opacity: 0; color: transparent;">{preheader}</div>
    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="background: #090e1a;">
      <tr>
        <td align="center" style="padding: 28px 12px;">
          <table class="email-shell" role="presentation" width="600" cellspacing="0" cellpadding="0" border="0" style="width: 600px; max-width: 600px; background: #10172a; border: 1px solid #202b47; border-radius: 16px; overflow: hidden;">
            <tr>
              <td style="height: 5px; background: #725cff; font-size: 0; line-height: 0;">&nbsp;</td>
            </tr>
            <tr>
              <td class="email-padding" style="padding: 34px 32px 28px;">
                <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0">
                  <tr>
                    <td style="color: #a99dff; font-size: 13px; font-weight: 800; letter-spacing: 1.5px; text-transform: uppercase;">◆ CryptoDigest</td>
                    <td style="color: #7f8aa5; font-size: 12px; text-align: right;">{report_date}</td>
                  </tr>
                </table>
                <h1 style="margin: 28px 0 10px; color: #ffffff; font-size: 30px; line-height: 37px;">Weekly Market Update</h1>
                <p style="margin: 0; color: #9ca8c2; font-size: 15px; line-height: 24px;">A focused snapshot of this week’s leading cryptocurrencies and their latest market movement.</p>
              </td>
            </tr>
            <tr>
              <td style="padding: 0 24px 12px;">
                <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0">
                  <tr>
                    <td style="color: #7f8aa5; font-size: 11px; font-weight: 700; letter-spacing: 1px; text-transform: uppercase;">Top {coin_count} by market capitalization</td>
                    <td style="color: #7f8aa5; font-size: 11px; text-align: right;">All values in USD</td>
                  </tr>
                </table>
              </td>
            </tr>
            {''.join(html_rows)}
            <tr>
              <td class="email-padding" style="padding: 18px 32px 30px; text-align: center;">
                <p style="margin: 0 0 8px; color: #697590; font-size: 11px; line-height: 18px;">Market data is informational and is not financial advice.</p>
                <p style="margin: 0; color: #7f8aa5; font-size: 12px; line-height: 18px;">Delivered weekly by <span style="color: #a99dff; font-weight: 700;">CryptoDigest</span></p>
              </td>
            </tr>
          </table>
        </td>
      </tr>
    </table>
  </body>
</html>"""

    return DigestContent(text_body="\n".join(text_lines), html_body=html_body)
