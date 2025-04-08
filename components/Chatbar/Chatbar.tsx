import { Conversation } from '@/types/chat';
import { KeyValuePair } from '@/types/data';
import { SupportedExportFormats } from '@/types/export';
import { IconFolderPlus, IconMessagesOff, IconPlus } from '@tabler/icons-react';
import { useTranslation } from 'next-i18next';
import { FC, useEffect, useState } from 'react';
import { Search } from '../Sidebar/Search';
import { ChatbarSettings } from './ChatbarSettings';
import { Conversations } from './Conversations';
import { File, Folder as Directory, Tree } from '../ui/file-tree';
import { useSetRecoilState, useRecoilState } from "recoil";
import { cardState, directoryState } from "@/utils/app/state";
import { useSession, signIn, signOut } from "next-auth/react";

interface FileInterface {
  owner: string | null | undefined;
  sharekey: string | null | undefined;
  filekey: string | null | undefined;
  name: string | null | undefined;
  createdAt: string | null | undefined;
  updatedAt: string | null | undefined;
  type: string | null | undefined;
}

type File = {
  owner: string | null | undefined;
  sharekey: string | null | undefined;
  name: string | null | undefined;
  filekey: string | null | undefined;
  type: string | null | undefined;
  createdAt: string | null | undefined;
  updatedAt: string | null | undefined;
};

interface FolderInterface {
  id: number | null | undefined;
  name: string | null | undefined;
  createdAt: string | null | undefined;
  updatedAt: string | null | undefined;
}

type Folder = {
  id: number | null | undefined;
  name: string | null | undefined;
  createdAt: string | null | undefined;
  updatedAt: string | null | undefined;
};

interface Props {
  folders: Folder[];
  files: File[];
  loading: boolean;
  conversations: Conversation[];
  selectedConversation: Conversation;
  apiKey: string;
  onNewConversation: () => void;
  onToggleLightMode: (mode: 'light' | 'dark') => void;
  onSelectConversation: (conversation: Conversation) => void;
  onDeleteConversation: (conversation: Conversation) => void;
  onUpdateConversation: (
    conversation: Conversation,
    data: KeyValuePair,
  ) => void;
  onApiKeyChange: (apiKey: string) => void;
  onClearConversations: () => void;
  onExportConversations: () => void;
  onImportConversations: (data: SupportedExportFormats) => void;
}

export const Chatbar: FC<Props> = ({
  folders,
  files,
  loading,
  conversations,
  selectedConversation,
  apiKey,
  onNewConversation,
  onSelectConversation,
  onDeleteConversation,
  onUpdateConversation,
  onApiKeyChange,
  onClearConversations,
  onExportConversations,
  onImportConversations,
}) => {
  const { t } = useTranslation('sidebar');
  const [searchTerm, setSearchTerm] = useState<string>('');
  const [filteredConversations, setFilteredConversations] = useState<Conversation[]>(conversations);
  const setCard = useSetRecoilState(cardState);
  const { data: session, status } = useSession();
  const [directory, setDirectory] = useRecoilState(directoryState);

  const handleUpdateConversation = (
    conversation: Conversation,
    data: KeyValuePair,
  ) => {
    onUpdateConversation(conversation, data);
    setSearchTerm('');
  };

  const handleDeleteConversation = (conversation: Conversation) => {
    onDeleteConversation(conversation);
    setSearchTerm('');
  };

  const handleDrop = (e: any) => {
    if (e.dataTransfer) {
      const conversation = JSON.parse(e.dataTransfer.getData('conversation'));
      onUpdateConversation(conversation, { key: 'folderId', value: 0 });

      e.target.style.background = 'none';
    }
  };

  const allowDrop = (e: any) => {
    e.preventDefault();
  };

  const highlightDrop = (e: any) => {
    e.target.style.background = '#343541';
  };

  const removeHighlight = (e: any) => {
    e.target.style.background = 'none';
  };

  // const ELEMENTS = [
  //   {
  //     id: "1",
  //     isSelectable: true,
  //     name: "src",
  //     children: [
  //       {
  //         id: "2",
  //         isSelectable: true,
  //         name: "app",
  //         children: [
  //           {
  //             id: "3",
  //             isSelectable: true,
  //             name: "layout.tsx",
  //           },
  //           {
  //             id: "4",
  //             isSelectable: true,
  //             name: "page.tsx",
  //           },
  //         ],
  //       },
  //       {
  //         id: "5",
  //         isSelectable: true,
  //         name: "components",
  //         children: [
  //           {
  //             id: "6",
  //             isSelectable: true,
  //             name: "header.tsx",
  //           },
  //           {
  //             id: "7",
  //             isSelectable: true,
  //             name: "footer.tsx",
  //           },
  //         ],
  //       },
  //       {
  //         id: "8",
  //         isSelectable: true,
  //         name: "lib",
  //         children: [
  //           {
  //             id: "9",
  //             isSelectable: true,
  //             name: "utils.ts",
  //           },
  //         ],
  //       },
  //     ],
  //   },
  // ];
  

  useEffect(() => {
    console.log("folders",folders);
    if (searchTerm) {
      setFilteredConversations(
        conversations.filter((conversation) => {
          const searchable =
            conversation.name.toLocaleLowerCase() +
            ' ' +
            conversation.messages.map((message) => message.content).join(' ');
          return searchable.toLowerCase().includes(searchTerm.toLowerCase());
        }),
      );
    } else {
      setFilteredConversations(conversations);
    }
  }, [searchTerm, conversations]);

  const [isUserMenuOpen, setIsUserMenuOpen] = useState(false);

  return (
    <div
      className={`fixed top-0 bottom-0 z-50 flex h-full w-[260px] flex-none flex-col space-y-2 bg-[#202123] p-2 transition-all sm:relative sm:top-0`}
    >
      <div className="flex items-center space-x-3">
                    {/* Profile */}
        <div className="items-center">
              {session && session.user ? (
                <div
                  onClick={() => setIsUserMenuOpen(!isUserMenuOpen)}
                  onMouseEnter={() => setIsUserMenuOpen(true)}
                  onMouseLeave={() => setIsUserMenuOpen(false)}
                >
                  <button
                    type="button"
                    className="flex rounded-full py-3"
                  >
                    <img
                      className="rounded-full w-11 h-11 hover:opacity-75"
                      src={session.user.image!}
                    ></img>
                  </button>
                  {/* Drop Down Menu */}
                  <div>
                    {isUserMenuOpen && (
                      <div
                        className="border-2 border-[#0D1F23] z-50 bg-[#253745] absolute right-2 min-w-40 text-base list-none divide-y divide-[#0D1F23] rounded-lg shadow "
                        id="user-dropdown"
                      >
                        <div className="px-4 py-4">
                          <span className="block text-sm text-white ">
                            {session.user.name}
                          </span>
                          <span className="block text-sm text-white truncate ">
                            {session.user.email}
                          </span>
                        </div>
                        <ul
                          className="flex flex-col items-center"
                          aria-labelledby="user-menu-button"
                        >
                          <li>
                            <button
                              className="h-8 px-4 m-2 text-sm bg-[#1e1e1e] text-white font-bold rounded "
                              onClick={() => {
                                signOut();
                              }}
                            >
                              Signout
                            </button>
                          </li>
                        </ul>
                      </div>
                    )}
                  </div>
                </div>
              ) : (
                <div>
                  {status === "loading" ? (
                    <div role="status" className="py-3">
                      <svg
                        aria-hidden="true"
                        className="w-11 h-11 text-[#5A636A] animate-spin fill-amber-600"
                        viewBox="0 0 100 101"
                        fill="none"
                        xmlns="http://www.w3.org/2000/svg"
                      >
                        <path
                          d="M100 50.5908C100 78.2051 77.6142 100.591 50 100.591C22.3858 100.591 0 78.2051 0 50.5908C0 22.9766 22.3858 0.59082 50 0.59082C77.6142 0.59082 100 22.9766 100 50.5908ZM9.08144 50.5908C9.08144 73.1895 27.4013 91.5094 50 91.5094C72.5987 91.5094 90.9186 73.1895 90.9186 50.5908C90.9186 27.9921 72.5987 9.67226 50 9.67226C27.4013 9.67226 9.08144 27.9921 9.08144 50.5908Z"
                          fill="currentColor"
                        />
                        <path
                          d="M93.9676 39.0409C96.393 38.4038 97.8624 35.9116 97.0079 33.5539C95.2932 28.8227 92.871 24.3692 89.8167 20.348C85.8452 15.1192 80.8826 10.7238 75.2124 7.41289C69.5422 4.10194 63.2754 1.94025 56.7698 1.05124C51.7666 0.367541 46.6976 0.446843 41.7345 1.27873C39.2613 1.69328 37.813 4.19778 38.4501 6.62326C39.0873 9.04874 41.5694 10.4717 44.0505 10.1071C47.8511 9.54855 51.7191 9.52689 55.5402 10.0491C60.8642 10.7766 65.9928 12.5457 70.6331 15.2552C75.2735 17.9648 79.3347 21.5619 82.5849 25.841C84.9175 28.9121 86.7997 32.2913 88.1811 35.8758C89.083 38.2158 91.5421 39.6781 93.9676 39.0409Z"
                          fill="currentFill"
                        />
                      </svg>
                      <span className="sr-only">Loading...</span>
                    </div>
                  ) : (
                    <button
                      className="bg-transparent border-2 mt-6 border-yellow-600 hover:bg-yellow-600 text-yellow-50 rounded-lg font-semibold hover:text-white py-1 px-3 my-4 mr-4"
                      onClick={() => signIn()}
                    >
                      Signin
                    </button>
                  )}
                </div>
              )}
            </div>
        <button
          className="flex w-fit flex-shrink-0 cursor-pointer select-none items-center gap-3 rounded-md border border-white/20 p-3 text-[14px] leading-normal text-white transition-colors duration-200 hover:bg-gray-500/10"
          onClick={() => {
            // onNewConversation();
            // setSearchTerm('');
            setCard({
              name: "UploadFile",
              shown: true,
              folderId: null,
              filekey: "",
              newName: null,
              fileType: null,
              sharedfiledelete: false,
            });
          }}
        >
          <IconPlus size={18} />
          {t('New Paper')}
        </button>

        <button
          className="ml-2 flex flex-shrink-0 cursor-pointer items-center gap-3 rounded-md border border-white/20 p-3 text-[14px] leading-normal text-white transition-colors duration-200 hover:bg-gray-500/10"
          // onClick={() => onCreateFolder(t('New folder'))}
          onClick={() => {
            // onNewConversation();
            // setSearchTerm('');
            setCard({
              name: "CreateFolder",
              shown: true,
              folderId: null,
              filekey: "",
              newName: null,
              fileType: null,
              sharedfiledelete: false,
            });
          }}
        >
          <IconFolderPlus size={18} />
        </button>
      </div>

      {conversations.length > 1 && (
        <Search
          placeholder="Search conversations..."
          searchTerm={searchTerm}
          onSearch={setSearchTerm}
        />
      )}

      <div className="flex-grow overflow-auto">

        {conversations.length > 0 ? (
          <div
            className="pt-2"
            onDrop={(e) => handleDrop(e)}
            onDragOver={allowDrop}
            onDragEnter={highlightDrop}
            onDragLeave={removeHighlight}
          >
            <Conversations
              loading={loading}
              conversations={filteredConversations.filter(
                (conversation) => !conversation.folderId,
              )}
              selectedConversation={selectedConversation}
              onSelectConversation={onSelectConversation}
              onDeleteConversation={handleDeleteConversation}
              onUpdateConversation={handleUpdateConversation}
            />
          </div>
        ) : (
          <div className="mt-8 flex flex-col items-center gap-3 text-sm leading-normal text-white opacity-50">
            <IconMessagesOff />
            {t('No conversations.')}
          </div>
        )}
    {directory.length > 0 && <div className="relative flex h-full w-full flex-col overflow-hidden rounded-lg border bg-[#1e1e1e]">
          <Tree
            className="overflow-hidden rounded-md p-2"
            elements={folders}
          >
            <Directory element={directory[directory.length-1].name ?? ''} value="1">
            {[...folders]
              .sort((a, b) => {
                const dateA = a.createdAt
                  ? new Date(a.createdAt)
                  : new Date(0);
                const dateB = b.createdAt
                  ? new Date(b.createdAt)
                  : new Date(0);
                return dateA.getTime() - dateB.getTime();
              })
              .map((folder: FolderInterface, index: number) => (
                <div onClick={()=>{
                  setDirectory((prevDirectory) => [
                    ...prevDirectory,
                    { id: folder.id, name: folder.name },
                  ]);
                }}>
                  <Directory value={index.toString()} element={folder.name || ''}/>
                </div>
              ))}
            {[...files]
                .sort((a, b) => {
                  const dateA = a.createdAt
                    ? new Date(a.createdAt)
                    : new Date(0);
                  const dateB = b.createdAt
                    ? new Date(b.createdAt)
                    : new Date(0);
                  return dateA.getTime() - dateB.getTime();
                })
                .map((file: FileInterface, index: number) => (
                  <File value={(index + folders.length).toString()}>
                    <p>{file.name}</p>
                  </File>
                ))}
            </Directory>
          </Tree>
        </div>}
      </div>

      <ChatbarSettings
        apiKey={apiKey}
        conversationsCount={conversations.length}
        onApiKeyChange={onApiKeyChange}
        onClearConversations={onClearConversations}
        onExportConversations={onExportConversations}
        onImportConversations={onImportConversations}
      />
    </div>
  );
};
