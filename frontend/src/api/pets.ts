import { apiRequest } from "./client";

export type PetType = "DOG" | "CAT";
export type PetGrowthStage = "STAGE_1" | "STAGE_2" | "STAGE_3";

export type VirtualPet = {
  pet_id: number;
  pet_type: PetType;
  pet_name: string;
  level: number;
  experience: number;
  next_level_experience: number;
  growth_stage: PetGrowthStage;
  health_percent: number;
  happiness_percent: number;
};

export type PetRewardTask = {
  task_type: string;
  title: string;
  reward_experience: number;
  is_completed: boolean;
};

export type PetRecentActivity = {
  activity_type: string;
  description: string;
  experience_delta: number;
  created_at: string;
};

export type VirtualPetStatus = {
  has_pet: boolean;
  pet: VirtualPet | null;
  today_tasks: PetRewardTask[];
  recent_activities: PetRecentActivity[];
};

export type CreateVirtualPetBody = {
  pet_type: PetType;
  pet_name: string;
};

export type VirtualPetCreateResponse = {
  pet_id: number;
  pet_type: PetType;
  pet_name: string;
  level: number;
  experience: number;
  growth_stage: PetGrowthStage;
};

export type VirtualPetNameUpdateResponse = {
  pet_id: number;
  pet_name: string;
};

export type PetRewardClaimResponse = {
  awarded_experience: number;
  claimed_task_count: number;
  level: number;
  experience: number;
  next_level_experience: number;
  growth_stage: PetGrowthStage;
};

export type PetCatalogSummary = {
  total_count: number;
  unlocked_count: number;
  completion_rate: number;
};

export type PetCatalogItem = {
  catalog_id: string;
  pet_type: PetType;
  display_name: string;
  is_unlocked: boolean;
  unlock_condition: string;
  affinity_score: number | null;
};

export type PetCatalog = {
  summary: PetCatalogSummary;
  items: PetCatalogItem[];
};

export async function getMyVirtualPet(token?: string) {
  return apiRequest<{ data: VirtualPetStatus }>("/virtual-pets", { token });
}

export async function createVirtualPet(body: CreateVirtualPetBody, token?: string) {
  return apiRequest<{ data: VirtualPetCreateResponse }>("/virtual-pets", {
    method: "POST",
    body: JSON.stringify(body),
    token,
  });
}

export async function updateVirtualPetName(petName: string, token?: string) {
  return apiRequest<{ data: VirtualPetNameUpdateResponse }>("/virtual-pets/me/name", {
    method: "PATCH",
    body: JSON.stringify({ pet_name: petName }),
    token,
  });
}

export async function claimVirtualPetRewards(token?: string) {
  return apiRequest<{ data: PetRewardClaimResponse }>("/virtual-pets/reward-tasks/claims", {
    method: "POST",
    token,
  });
}

export async function getPetCatalog(petType?: PetType, token?: string) {
  const query = petType ? `?pet_type=${petType}` : "";
  return apiRequest<{ data: PetCatalog }>(`/virtual-pets/catalog${query}`, { token });
}
