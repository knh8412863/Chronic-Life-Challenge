from app.services.email import _mask_token


def test_mask_token_hides_original_token_body():
    token = "abcdefghijklmnopqrstuvwxyz123456"

    masked = _mask_token(token)

    assert masked == "***123456"
    assert token not in masked
    assert "abcdef" not in masked


def test_mask_token_hides_short_token_completely():
    assert _mask_token("short") == "***"
