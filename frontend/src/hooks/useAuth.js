import { useDispatch, useSelector } from "react-redux";
import {
  loginSuccess,
  logout,
} from "../store/authSlice";

export default function useAuth() {
  const dispatch = useDispatch();

  const auth = useSelector(
    (state) => state.auth
  );

  const login = (token, user) => {
    localStorage.setItem("token", token);

    dispatch(
      loginSuccess({
        token,
        user,
      })
    );
  };

  const signOut = () => {
    dispatch(logout());
  };

  return {
    ...auth,
    login,
    signOut,
  };
}
