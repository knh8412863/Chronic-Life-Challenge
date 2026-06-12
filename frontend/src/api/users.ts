import { apiRequest } from "./client";

export type Gender = "MALE" | "FEMALE";
export type ConsentType = "TOS" | "PRIVACY" | "HEALTH_DATA" | "MARKETING" | "LOCATION";
export type WithdrawalReason = "NOT_USEFUL" | "PRIVACY_CONCERN" | "HARD_TO_USE" | "FOUND_ALTERNATIVE" | "OTHER";

type MaybeData<T> = T | { data: T };

function unwrapData<T>(response: MaybeData<T>): T {
  if (response && typeof response === "object" && "data" in response) {
    return response.data;
  }
  return response;
}

export type UserInfo = {
  id: number;
  name: string;
  email: string;
  phone_number: string;
  birthday: string;
  gender: Gender;
  profile_image_url: string | null;
  height: number | null;
  weight: number | null;
  bmi: number | null;
  managed_diseases: string[];
  joined_days: number;
  membership_grade: string;
  points: number;
  level: number;
  created_at: string;
};

export type UserUpdatePayload = {
  name?: string;
  phone_number?: string;
  height?: number;
  weight?: number;
  profile_image_url?: string | null;
  managed_diseases?: string[];
};

export type UserConsent = {
  consent_type: ConsentType;
  title: string;
  is_required: boolean;
  is_agreed: boolean;
  agreed_at: string | null;
  withdrawn_at: string | null;
  policy_version: string;
};

export type PolicyChange = {
  policy_type: ConsentType;
  title: string;
  policy_version: string;
  changed_at: string | null;
};

export type ConsentList = {
  items: UserConsent[];
  recent_policy_changes: PolicyChange[];
};

export type PolicyDocument = {
  policy_type: ConsentType;
  title: string;
  policy_version: string;
  changed_at: string | null;
  content: string;
};

const POLICY_CONTENTS: Record<ConsentType, { title: string; isRequired: boolean; content: string }> = {
  TOS: {
    title: "[필수] 서비스 이용약관",
    isRequired: true,
    content: `제1조 (목적)
본 약관은 ALL4Health(이하 "회사")가 제공하는 All4Health Chronic Care 서비스(이하 "서비스")의 이용 조건 및 절차, 회사와 회원 간의 권리, 의무 및 책임 사항을 규정함을 목적으로 합니다.

제2조 (이용계약의 성립)
이용계약은 회원이 본 약관에 동의하고 회사가 제시한 회원가입 절차를 완료함으로써 성립합니다.
회사는 서비스의 안정적 제공을 위해 만 14세 미만 아동의 회원가입을 제한할 수 있습니다.

제3조 (서비스의 제공 및 변경)
회사는 회원에게 만성질환 관리, 건강 기록 모니터링, 맞춤형 건강 콘텐츠 제공 등의 서비스를 제공합니다.
본 서비스는 의료법상의 '의료행위'가 아니며, 서비스 내에서 제공되는 피드백과 정보는 의사의 전문적인 진단이나 치료를 대신할 수 없습니다.

제4조 (회원의 의무 및 탈퇴)
회원은 타인의 정보를 도용하여 가입할 수 없으며, 본인의 건강 데이터를 정확하게 입력해야 합니다.
회원은 언제든지 서비스 내 회원탈퇴 기능을 통해 이용계약을 해지할 수 있으며, 탈퇴 시 관련 법령에 따라 회원 정보가 처리됩니다.`,
  },
  PRIVACY: {
    title: "[필수] 개인정보 처리방침",
    isRequired: true,
    content: `수집하는 개인정보 항목
회원가입 시 (필수): 이메일 주소(아이디), 비밀번호, 이름, 생년월일, 성별
서비스 이용 과정 생성 정보: 서비스 이용 기록, 접속 로그, 쿠키, 기기 정보(OS, 모델명)

개인정보의 수집 및 이용 목적
이용자 식별 및 본인 확인, 회원제 서비스 제공
만성질환 관리 서비스 고도화 및 시스템 안정성 유지
고객 문의 응대, 고지사항 및 알림 전달

개인정보의 보유 및 이용 기간
회원 탈퇴 시 즉시 파기하는 것을 원칙으로 합니다.
단, 관계 법령(통신비밀보호법 등)의 규정에 의하여 보존할 필요가 있는 경우, 해당 법령에서 정한 기간 동안 안전하게 보관 후 파기합니다.`,
  },
  HEALTH_DATA: {
    title: "[필수] 건강 데이터 수집·이용 동의",
    isRequired: true,
    content: `(※ 만성질환 관리 서비스의 특성상 혈당, 혈압, 기저질환 등은 법적으로 '민감정보'로 분류되므로, 일반 개인정보와 별도로 분리하여 필수 동의를 받아야 합니다.)

ALL4Health 서비스 제공을 위한 민감정보(건강정보) 처리 동의

수집·이용하는 민감정보 항목
회원이 직접 입력하거나 기기를 연동하여 수집한 기저질환 정보, 혈당·혈압 등 생체 인식 데이터, 투약 기록, 식단 및 운동량 기록, 서비스 이용 중 생성된 건강 데이터 일체

수집 및 이용 목적
개인 맞춤형 만성질환 관리 서비스 제공 (건강 데이터 모니터링, 추이 분석, 맞춤형 건강 가이드라인 및 피드백 리포트 생성 등)

보유 및 이용 기간
회원 탈퇴 시 즉시 파기

귀하는 본 동의를 거부할 권리가 있습니다. 다만, 본 동의는 만성질환 관리 서비스 제공을 위한 최소한의 필수 사항이므로, 동의를 거부하실 경우 서비스 이용이 불가능합니다.`,
  },
  MARKETING: {
    title: "[선택] 마케팅 정보 수신 동의",
    isRequired: false,
    content: `마케팅 목적 개인정보 이용 및 광고성 정보 수신 동의

수집 및 이용 목적
ALL4Health가 제공하는 신규 서비스 및 기능 안내, 맞춤형 혜택 정보 제공, 건강 관련 이벤트 및 프로모션 광고성 정보 발송

수집 항목
이메일 주소, 서비스 이용 기록

보유 및 이용 기간
회원 탈퇴 시 또는 마케팅 동의 철회 시까지

귀하는 본 동의를 거부할 권리가 있으며, 거부하더라도 ALL4Health의 핵심 만성질환 관리 서비스 이용에는 아무런 제한이 없습니다.`,
  },
  LOCATION: {
    title: "[선택] 위치기반 서비스 이용 동의",
    isRequired: false,
    content: "현재 위치기반 서비스는 MVP 범위에 포함되지 않습니다.",
  },
};

export function getLocalPolicyDocument(policyType: ConsentType, version = "v1.0"): PolicyDocument {
  const policy = POLICY_CONTENTS[policyType];
  return {
    policy_type: policyType,
    title: policy.title,
    policy_version: version,
    changed_at: null,
    content: policy.content,
  };
}

function getLocalConsents(): ConsentList {
  return {
    items: (["TOS", "PRIVACY", "HEALTH_DATA", "MARKETING"] as ConsentType[]).map((type) => ({
      consent_type: type,
      title: POLICY_CONTENTS[type].title,
      is_required: POLICY_CONTENTS[type].isRequired,
      is_agreed: POLICY_CONTENTS[type].isRequired,
      agreed_at: null,
      withdrawn_at: null,
      policy_version: "v1.0",
    })),
    recent_policy_changes: [],
  };
}

export type WithdrawalPayload = {
  password: string;
  withdrawal_reason: WithdrawalReason;
  withdrawal_comment?: string | null;
  confirm_agreed: boolean;
};

export type PasswordChangePayload = {
  current_password: string;
  new_password: string;
  new_password_confirm: string;
};

export async function getCurrentUser(token?: string) {
  const response = await apiRequest<MaybeData<UserInfo>>("/users/me", { token });
  return unwrapData(response);
}

export async function updateCurrentUser(payload: UserUpdatePayload, token?: string) {
  const response = await apiRequest<MaybeData<UserInfo>>("/users/me", {
    method: "PATCH",
    body: JSON.stringify(payload),
    token,
  });
  return unwrapData(response);
}

export async function withdrawCurrentUser(payload: WithdrawalPayload, token?: string) {
  return apiRequest<void>("/users/me", {
    method: "DELETE",
    body: JSON.stringify(payload),
    token,
  });
}

export async function verifyCurrentUserPassword(password: string, token?: string) {
  return apiRequest<void>("/users/me/password-verification", {
    method: "POST",
    body: JSON.stringify({ password }),
    token,
  });
}

export async function changeCurrentUserPassword(payload: PasswordChangePayload, token?: string) {
  return apiRequest<void>("/users/me/password", {
    method: "PATCH",
    body: JSON.stringify(payload),
    token,
  });
}

export async function getUserConsents(token?: string) {
  try {
    const response = await apiRequest<MaybeData<ConsentList>>("/users/me/consents", { token });
    return unwrapData(response);
  } catch {
    return getLocalConsents();
  }
}

export async function updateUserConsent(consentType: ConsentType, isAgreed: boolean, policyVersion: string, token?: string) {
  const response = await apiRequest<MaybeData<UserConsent>>(`/users/me/consents/${consentType}`, {
    method: "PATCH",
    body: JSON.stringify({ is_agreed: isAgreed, policy_version: policyVersion }),
    token,
  });
  return unwrapData(response);
}

export async function getPolicyDocument(policyType: ConsentType, version?: string, token?: string) {
  const query = version ? `?version=${encodeURIComponent(version)}` : "";
  try {
    const response = await apiRequest<MaybeData<PolicyDocument>>(`/policy-documents/${policyType}${query}`, { token });
    return unwrapData(response);
  } catch {
    return getLocalPolicyDocument(policyType, version);
  }
}
