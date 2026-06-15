import passwordHiddenIcon from "../../assets/icon/비밀번호 안보이게.png";
import passwordVisibleIcon from "../../assets/icon/비밀번호 보이게.png";

type PasswordToggleButtonProps = {
  isVisible: boolean;
  onToggle: () => void;
  size?: number;
};

export function PasswordToggleButton({ isVisible, onToggle, size = 18 }: PasswordToggleButtonProps) {
  return (
    <button
      type="button"
      aria-label={isVisible ? "비밀번호 숨기기" : "비밀번호 보기"}
      onClick={onToggle}
      style={{
        position: "absolute",
        right: 10,
        top: "50%",
        transform: "translateY(-50%)",
        width: size + 6,
        height: size + 6,
        border: "none",
        background: "transparent",
        padding: 0,
        cursor: "pointer",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
      }}
    >
      <img
        src={isVisible ? passwordVisibleIcon : passwordHiddenIcon}
        alt=""
        aria-hidden="true"
        style={{ width: size, height: size, objectFit: "contain", display: "block" }}
      />
    </button>
  );
}
