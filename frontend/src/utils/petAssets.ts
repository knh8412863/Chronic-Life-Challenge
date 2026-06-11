import capybaraStage1 from "../assets/mypet/capybara_1.png";
import capybaraStage2 from "../assets/mypet/capybara_2.png";
import capybaraStage3 from "../assets/mypet/capybara_3.png";
import catStage1 from "../assets/mypet/cat_1.png";
import catStage2 from "../assets/mypet/cat_2.png";
import catStage3 from "../assets/mypet/cat_3.png";
import dogStage1 from "../assets/mypet/dog_1.png";
import dogStage2 from "../assets/mypet/dog_2.png";
import dogStage3 from "../assets/mypet/dog_3.png";
import hamsterStage1 from "../assets/mypet/hamster_1.png";
import hamsterStage2 from "../assets/mypet/hamster_2.png";
import hamsterStage3 from "../assets/mypet/hamster_3.png";
import rabbitStage1 from "../assets/mypet/rabbit_1.png";
import rabbitStage2 from "../assets/mypet/rabbit_2.png";
import rabbitStage3 from "../assets/mypet/rabbit_3.png";

import type { PetGrowthStage, PetType } from "../api/pets";

export const PET_TYPES: PetType[] = ["DOG", "CAT", "RABBIT", "CAPYBARA", "HAMSTER"];

export const PET_META: Record<PetType, {
  label: string;
  emoji: string;
  desc: string;
  features: string[];
}> = {
  DOG: {
    label: "강아지",
    emoji: "🐶",
    desc: "충성스럽고 활발한 동반자",
    features: ["운동 활동 보너스 +20%", "일일 활동 점수 강화", "산책 챌린지 특화"],
  },
  CAT: {
    label: "고양이",
    emoji: "🐱",
    desc: "독립적이고 차분한 동반자",
    features: ["건강 일지 보너스 +20%", "일상 기록 습관 강화", "생활습관 챌린지 특화"],
  },
  RABBIT: {
    label: "토끼",
    emoji: "🐰",
    desc: "가볍고 꾸준한 루틴 메이트",
    features: ["혈압 측정 보너스 +20%", "아침 기록 습관 강화", "기초 건강 체크 특화"],
  },
  CAPYBARA: {
    label: "카피바라",
    emoji: "🦫",
    desc: "차분하게 페이스를 지켜주는 친구",
    features: ["수분 챌린지 보너스 +20%", "스트레스 관리 루틴 강화", "꾸준함 챌린지 특화"],
  },
  HAMSTER: {
    label: "햄스터",
    emoji: "🐹",
    desc: "작은 성취를 모아 성장하는 친구",
    features: ["건강 일지 보너스 +10%", "짧은 기록 루틴 강화", "습관 누적 특화"],
  },
};

const PET_IMAGES: Partial<Record<PetType, [string, string, string]>> = {
  DOG: [dogStage1, dogStage2, dogStage3],
  CAT: [catStage1, catStage2, catStage3],
  RABBIT: [rabbitStage1, rabbitStage2, rabbitStage3],
  CAPYBARA: [capybaraStage1, capybaraStage2, capybaraStage3],
  HAMSTER: [hamsterStage1, hamsterStage2, hamsterStage3],
};

export function petStageIndex(stage?: PetGrowthStage) {
  if (stage === "STAGE_3") return 2;
  if (stage === "STAGE_2") return 1;
  return 0;
}

export function getPetImage(type: PetType, stage: PetGrowthStage = "STAGE_1") {
  return PET_IMAGES[type]?.[petStageIndex(stage)] ?? null;
}
