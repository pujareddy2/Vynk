export type UIState = {
  isLoading: boolean;
  error: string | null;
  activeDialog: string | null;
  isDrawerOpen: boolean;
};

export const initialUIState: UIState = {
  isLoading: false,
  error: null,
  activeDialog: null,
  isDrawerOpen: false,
};