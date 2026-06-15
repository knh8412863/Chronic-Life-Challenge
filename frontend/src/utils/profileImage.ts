export const profileImageUpdatedEvent = "all4health:profile-image-updated";

const profileImageStoragePrefix = "all4health.profileImage.";
const maxProfileImageSize = 480;
const profileImageQuality = 0.86;

export function profileImageStorageKey(userId: number) {
  return `${profileImageStoragePrefix}${userId}`;
}

export function getStoredProfileImage(userId: number) {
  return localStorage.getItem(profileImageStorageKey(userId));
}

export function setStoredProfileImage(userId: number, dataUrl: string) {
  localStorage.setItem(profileImageStorageKey(userId), dataUrl);
  window.dispatchEvent(
    new CustomEvent(profileImageUpdatedEvent, {
      detail: { userId, profileImageUrl: dataUrl },
    }),
  );
}

export async function resizeProfileImageFile(file: File): Promise<string> {
  const imageUrl = URL.createObjectURL(file);
  try {
    const image = await new Promise<HTMLImageElement>((resolve, reject) => {
      const img = new Image();
      img.onload = () => resolve(img);
      img.onerror = () => reject(new Error("이미지를 불러오지 못했습니다."));
      img.src = imageUrl;
    });

    const scale = Math.min(1, maxProfileImageSize / Math.max(image.width, image.height));
    const width = Math.max(1, Math.round(image.width * scale));
    const height = Math.max(1, Math.round(image.height * scale));
    const canvas = document.createElement("canvas");
    canvas.width = width;
    canvas.height = height;
    const context = canvas.getContext("2d");
    if (!context) {
      throw new Error("이미지 변환을 준비하지 못했습니다.");
    }
    context.drawImage(image, 0, 0, width, height);
    return canvas.toDataURL("image/jpeg", profileImageQuality);
  } finally {
    URL.revokeObjectURL(imageUrl);
  }
}
