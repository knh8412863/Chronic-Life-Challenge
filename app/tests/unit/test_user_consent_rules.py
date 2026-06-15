from datetime import date, datetime
from types import SimpleNamespace

from app.models.users import ConsentType
from app.services.users import UserManageService


def test_consent_list_includes_required_and_optional_items():
    agreed_at = datetime(2026, 6, 4, 10, 0)
    consent_map = {
        ConsentType.TOS: SimpleNamespace(
            is_agreed=True,
            agreed_at=agreed_at,
            withdrawn_at=None,
            policy_version="v1.0",
        ),
        ConsentType.MARKETING: SimpleNamespace(
            is_agreed=False,
            agreed_at=None,
            withdrawn_at=agreed_at,
            policy_version="v1.0",
        ),
    }
    documents = [
        SimpleNamespace(
            policy_type=ConsentType.PRIVACY,
            title="개인정보 처리방침",
            policy_version="v1.2",
            changed_at=date(2026, 3, 1),
        )
    ]

    result = UserManageService._build_consent_list(consent_map, documents)

    assert len(result.items) == 5
    assert result.items[0].consent_type == "TOS"
    assert result.items[0].is_required is True
    assert result.items[0].is_agreed is True
    assert result.items[3].consent_type == "MARKETING"
    assert result.items[3].is_required is False
    assert result.items[3].is_agreed is False
    assert result.items[4].consent_type == "LOCATION"
    assert result.items[4].is_agreed is False
    assert result.recent_policy_changes[0].policy_version == "v1.2"


def test_missing_required_consent_is_displayed_as_agreed_by_policy():
    item = UserManageService._to_consent_item(ConsentType.PRIVACY, consent=None)

    assert item.title == "개인정보 처리방침"
    assert item.is_required is True
    assert item.is_agreed is True
    assert item.policy_version == "v1.0"


def test_missing_optional_consent_is_displayed_as_not_agreed():
    item = UserManageService._to_consent_item(ConsentType.LOCATION, consent=None)

    assert item.title == "위치 기반 서비스 이용약관"
    assert item.is_required is False
    assert item.is_agreed is False


def test_default_policy_document_returns_modal_content():
    result = UserManageService._default_policy_document(ConsentType.MARKETING, version="v1.1")

    assert result.policy_type == "MARKETING"
    assert result.title == "마케팅 정보 수신 동의"
    assert result.policy_version == "v1.1"
    assert "마케팅 목적 개인정보 이용" in result.content
    assert "동의를 거부할 권리" in result.content
