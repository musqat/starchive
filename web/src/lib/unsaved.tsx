"use client";

import { createContext, useContext } from "react";

/** 드로어가 닫히기 전에 물어볼지 알려준다. 단독 페이지에는 드로어가 없어 아무 일도 하지 않는다 */
export const UnsavedContext = createContext<(dirty: boolean) => void>(() => {});

export const useUnsaved = () => useContext(UnsavedContext);
