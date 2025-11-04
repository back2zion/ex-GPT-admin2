import { useToastStore } from "@store/toastStore";

export const showToast = ({ message, type = "success", timer = 4000 }) => {
  const addToast = useToastStore.getState().addToast;
  addToast({ message, type, timer });
};
