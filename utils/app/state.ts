import { atom } from "recoil";

// CARD STATE
type card = {
  name: string;
  shown: boolean;
  filekey: string | null | undefined;
  fileType: string | null | undefined;
  folderId: number | null | undefined;
  newName: string | null | undefined;
  sharedfiledelete: boolean;
};
export const cardState = atom<card>({
  key: "cardkey",
  default: {
    name: "",
    shown: false,
    filekey: "",
    fileType: null,
    folderId: null,
    newName: undefined,
    sharedfiledelete: false,
  },
});

// CURRENT DIRECTORY STATE
type Directory = {
  id: number | null | undefined;
  name: string | null | undefined;
};
export const directoryState = atom<Directory[]>({
  key: "recoil_directory",
  default: [],
});

// FOLDER STATE
type Folder = {
  id: number | null | undefined;
  name: string | null | undefined;
  createdAt: string | null | undefined;
  updatedAt: string | null | undefined;
};
export const folderState = atom<Folder[]>({
  key: "recoil_folderList",
  default: [],
});

// FILE STATE
type File = {
  owner: string | null | undefined;
  sharekey: string | null | undefined;
  name: string | null | undefined;
  filekey: string | null | undefined;
  type: string | null | undefined;
  createdAt: string | null | undefined;
  updatedAt: string | null | undefined;
};
export const fileState = atom<File[]>({
  key: "recoil_fileList",
  default: [],
});

export const selectedFileState = atom<File|null>({
  key: "recoil_selectedFile",
  default: null
});

//  USER STATE
type User = {
  name: string | null | undefined;
  email: string | null | undefined;
  id: string | null | undefined;
  fileLimit: number | null | undefined;
};

export const userState = atom<User>({
  key: "userState",
  default: {
    name: null,
    email: null,
    id: null,
    fileLimit: null,
  },
});

// MAIN FOLDER STATE
export const mainFolderState = atom({
  key: "recoil_mainFolder",
  default: "root",
});

// FOLDER CREATION STATE
export const updationState = atom({
  key: "recoil_rootUpdation",
  default: false,
});

// Message State
export const messageState = atom({
  key: "recoil_message",
  default: {
    open: false,
    text: "",
    type: "success",
  },
});
