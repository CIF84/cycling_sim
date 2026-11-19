import { useEffect, useState } from "react";
import { DEFAULT_GROUPSET_ID } from "../model/gearing";
import { DEFAULT_INPUTS, type Inputs } from "../model/types";
import { forgetSetup, loadSetup, saveSetup, SETUP_KEY } from "./savedSetup";

type Status =
  | "off"
  | "saved"
  | "invalid"
  | "unavailable"
  | "discarded"
  | "forgotten"
  | "remove-error";

export function useRememberedSetup() {
  const [initial] = useState(loadSetup);
  const [inputs, setInputs] = useState<Inputs>(
    () => initial.setup?.inputs ?? { ...DEFAULT_INPUTS },
  );
  const [groupsetId, setGroupsetId] = useState(
    initial.setup?.groupsetId ?? DEFAULT_GROUPSET_ID,
  );
  const [remember, setRemember] = useState(initial.status === "saved");
  const [status, setStatus] = useState<Status>(
    initial.status === "invalid" ? "discarded" : initial.status,
  );

  useEffect(() => {
    if (remember) setStatus(saveSetup(inputs, groupsetId));
  }, [remember, inputs, groupsetId]);

  useEffect(() => {
    function onStorage(event: StorageEvent) {
      // Forgetting in another tab must not be undone by this tab's next edit.
      if (
        (event.key === SETUP_KEY || event.key === null) &&
        event.newValue === null
      ) {
        setRemember(false);
        setStatus("forgotten");
      }
    }
    window.addEventListener("storage", onStorage);
    return () => window.removeEventListener("storage", onStorage);
  }, []);

  function changeRemember(checked: boolean) {
    if (checked) {
      setRemember(true);
    } else {
      // Revoking consent stops future writes even if deletion is blocked.
      setRemember(false);
      setStatus(forgetSetup() ? "forgotten" : "remove-error");
    }
  }

  return {
    inputs,
    setInputs,
    groupsetId,
    setGroupsetId,
    remember,
    changeRemember,
    status,
  };
}
