import { useToastStore } from "../../store/toastStore";
import Toast from "./Toast";

const ToastContainer = () => {
  const toasts = useToastStore(state => state.toasts);
  const removeToast = useToastStore(state => state.removeToast);

  return (
    <div className="toast-container">
      {toasts.map(toast => (
        <Toast
          key={toast.id}
          type={toast.type}
          message={toast.message}
          timer={toast.timer || 4000}
          onClose={() => removeToast(toast.id)}
        />
      ))}
    </div>
  );
};

export default ToastContainer;
