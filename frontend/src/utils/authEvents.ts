export const userSessionUpdatedEvent = "all4health:user-session-updated";

export function notifyUserSessionUpdated() {
  window.dispatchEvent(new CustomEvent(userSessionUpdatedEvent));
}
