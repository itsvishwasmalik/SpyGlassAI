
import { Chatbar } from '@/components/Chatbar/Chatbar';
import { Navbar } from '@/components/Mobile/Navbar';
import { Promptbar } from '@/components/Promptbar/Promptbar';
import { Conversation, Message } from '@/types/chat';
import { IconArrowBarLeft, IconArrowBarRight } from '@tabler/icons-react';
import Head from 'next/head';
import { useEffect, useRef, useState } from 'react';
import { useRecoilState, useRecoilValue } from "recoil";
import {
  cardState,
  fileState,
  folderState,
  userState,
  directoryState,
  mainFolderState,
  updationState,
  messageState,
  selectedFileState
} from "@/utils/app/state";
import axios from "axios";
import { useRouter } from "next/router";
import { useSession } from "next-auth/react";
import Signin from "@/components/Cards/Signin";
import CreateFolder from "@/components/Cards/CreateFolder";
import UploadFile from "@/components/Cards/UploadFile";
import Delete from "@/components/Cards/Delete";
import Rename from "@/components/Cards/Rename";
import Share from "@/components/Cards/Share";
import { Chat } from "@/components/Chat";



const Home = () => {
  // STATE ----------------------------------------------
  const [apiKey, setApiKey] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(false);
  const [lightMode, setLightMode] = useState<'dark' | 'light'>('dark');
  const [messageIsStreaming, setMessageIsStreaming] = useState<boolean>(false);

  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [selectedConversation, setSelectedConversation] =useState<Conversation>();

  const [showSidebar, setShowSidebar] = useState<boolean>(true);
  const [showPromptbar, setShowPromptbar] = useState<boolean>(true);

  // BASIC HANDLERS --------------------------------------------

  const handleToggleChatbar = () => {
    setShowSidebar(!showSidebar);
    localStorage.setItem('showChatbar', JSON.stringify(!showSidebar));
  };

  const handleTogglePromptbar = () => {
    setShowPromptbar(!showPromptbar);
    localStorage.setItem('showPromptbar', JSON.stringify(!showPromptbar));
  };

  const { data: session, status } = useSession();
  const [card, setCard] = useRecoilState(cardState);
  const [user, setUser] = useRecoilState(userState);
  const [files, setFiles] = useRecoilState(fileState);
  const [folders, setFolders] = useRecoilState(folderState);
  const [directory, setDirectory] = useRecoilState(directoryState);
  const [mainFolder, setMainFolder] = useRecoilState(mainFolderState);
  const updation = useRecoilValue(updationState);
  const [message, setMessage] = useRecoilState(messageState);
  const router = useRouter();
  const [paperDetails, setPaperDetails] = useState<any>(undefined);
  const [selectedFile, setSelectedFile] = useRecoilState(selectedFileState);

  // GET ALL FOLDERS IN CURRENT FOLDER
  async function getFolders() {
    // console.log("inside get folders");
    try {
      // console.log("parent folder id: ", directory[directory.length - 1].id);
      await axios
        .post("/api/db/folder/getallfolder", {
          parentFolderId: directory[directory.length - 1].id,
          userId: user.id,
        })
        .then((res) => {
          // console.log("folders: ", res.data.folders);
          setFolders(res.data.folders);
        });
    } catch (error) {
      console.error("Error fetching all folders:", error);
    }
  }

  // GET ALL FILES IN CURRENT FOLDER
  async function getFiles() {
    // console.log("inside get files");
    try {
      await axios
        .post("/api/db/file/getallfile", {
          userId: user.id,
          folderId: directory[directory.length - 1].id,
        })
        .then((res) => {
          // console.log("files: ", res.data.files);
          setFiles(res.data.files);
          setLoading(false);
        });
    } catch (error) {
      console.error("Error fetching all files:", error);
    }
  }

  // CREATE ROOT FOLDER FUNCTION
  async function createRootFolder() {
    // console.log("inside create root folder");
    try {
      await axios
        .post("/api/db/folder/createfolder", {
          userId: user.id,
          folderName: "root",
        })
        .then((res) => {
          // console.log("created root folder: ", res.data);
          setDirectory([{ id: res.data.folderId, name: "root" }]);
        });
    } catch (error) {
      console.error("Error creating root folders:", error);
    }
  }

  //  GET MAIN FOLDER (ROOT, SHARED) ID
  async function getMainFolder(folderName: string) {
    // console.log("inside get main folder");
    try {
      await axios
        .post("/api/db/folder/getmainfolder", {
          userId: user.id,
          folderName: folderName,
        })
        .then((res) => {
          if (res.data) {
            // console.log(mainFolder, " folder exists: ", res.data.id);
            setDirectory([{ id: res.data.id, name: mainFolder }]);
          } else if (mainFolder === "root") {
            // console.log(
            //   mainFolder,
            //   " folder does not exist. Creating root folder..."
            // );
            createRootFolder();
          } else if (mainFolder === "shared") {
            setMessage({
              text: "Nothing shared with you yet!",
              open: true,
              type: "error",
            });
            setTimeout(() => {
              setMessage({ text: "", open: false, type: "" });
            }, 2000);
            setMainFolder("root");
            setLoading(false);
          }
        });
    } catch (error) {
      console.log("Error fetching main folder:", error);
      console.error("Error fetching main folder:", error);
    }
  }

  // GET USER ID FUNCTION
  async function getUserId() {
    // console.log("inside get user id");
    try {
      await axios
        .post("/api/db/user/getuserid", {
          email: session?.user?.email,
        })
        .then((res) => {
          setUser({
            id: res.data.id,
            name: session?.user?.name,
            email: session?.user?.email,
            fileLimit: res.data.fileLimit,
          });
          // console.log("user id: ", res.data);
        });
    } catch (error) {
      console.error("Error fetching user id", error);
    }
  }
  useEffect(() => {
    // console.log("sign in use effect");
    //Signin Card
    if (status === "unauthenticated") {
      setCard({
        name: "signin",
        shown: true,
        folderId: null,
        filekey: null,
        newName: null,
        fileType: null,
        sharedfiledelete: false,
      });
    } else if (!user.id && session?.user?.email) {
      setLoading(true);
      getUserId();
    } else {
      setCard({
        name: "",
        shown: false,
        folderId: null,
        filekey: null,
        newName: null,
        fileType: null,
        sharedfiledelete: false,
      });
    }
  }, [session]);

  useEffect(() => {
    // console.log(directory,"directory useeffect");
    // console.log(mainFolder);
    if (user.id && mainFolder === "root" && directory.length === 0)
      getMainFolder(mainFolder);
    if (user.id && mainFolder === "shared") getMainFolder(mainFolder);
  }, [user, mainFolder]);

  useEffect(() => {
    // console.log("files loading useeffect");
    if (user.id) {
      setLoading(true);
      if (directory.length > 0) {
        getFolders().then(() => {
          getFiles();
        });
      }
    }
  }, [updation, directory]);

  // Pick a static json file from the public folder
  // const getPaperDetails = () => {
  //   const jsonData = require('../public/json/temp.json');
  //   const paperDetails = jsonData.research_paper_details;
  //   return paperDetails;
  // }

  const handleSend = async (
    message: Message,
    deleteCount = 0,
  ) => {
    if (selectedConversation) {
      let updatedConversation: Conversation;

      if (deleteCount) {
        const updatedMessages = [...selectedConversation.messages];
        for (let i = 0; i < deleteCount; i++) {
          updatedMessages.pop();
        }

        updatedConversation = {
          ...selectedConversation,
          messages: [...updatedMessages, message],
        };
      } else {
        updatedConversation = {
          ...selectedConversation,
          messages: [...selectedConversation.messages, message],
        };
      }

      setSelectedConversation(updatedConversation);
      setLoading(true);
      setMessageIsStreaming(true);

      // const chatBody: ChatBody = {
      //   model: updatedConversation.model,
      //   messages: updatedConversation.messages,
      //   key: apiKey,
      //   prompt: updatedConversation.prompt,
      // };

      // const endpoint = 'api/chat';
      // let body;
      // body = JSON.stringify(chatBody);

      // const controller = new AbortController();
      // const response = await fetch(endpoint, {
      //   method: 'POST',
      //   headers: {
      //     'Content-Type': 'application/json',
      //   },
      //   signal: controller.signal,
      //   body,
      // });

      // if (!response.ok) {
      //   setLoading(false);
      //   setMessageIsStreaming(false);
      //   toast.error(response.statusText);
      //   return;
      // }

      // const data = response.body;

      // if (!data) {
      //   setLoading(false);
      //   setMessageIsStreaming(false);
      //   return;
      // }

      //   if (updatedConversation.messages.length === 1) {
      //     const { content } = message;
      //     const customName =
      //       content.length > 30 ? content.substring(0, 30) + '...' : content;

      //     updatedConversation = {
      //       ...updatedConversation,
      //       name: customName,
      //     };
      //   }

      //   setLoading(false);

      //   const reader = data.getReader();
      //   const decoder = new TextDecoder();
      //   let done = false;
      //   let isFirst = true;
      //   let text = '';

      //   while (!done) {
      //     if (stopConversationRef.current === true) {
      //       controller.abort();
      //       done = true;
      //       break;
      //     }
      //     const { value, done: doneReading } = await reader.read();
      //     done = doneReading;
      //     const chunkValue = decoder.decode(value);

      //     text += chunkValue;

      //     if (isFirst) {
      //       isFirst = false;
      //       const updatedMessages: Message[] = [
      //         ...updatedConversation.messages,
      //         { role: 'assistant', content: chunkValue },
      //       ];

      //       updatedConversation = {
      //         ...updatedConversation,
      //         messages: updatedMessages,
      //       };

      //       setSelectedConversation(updatedConversation);
      //     } else {
      //       const updatedMessages: Message[] = updatedConversation.messages.map(
      //         (message, index) => {
      //           if (index === updatedConversation.messages.length - 1) {
      //             return {
      //               ...message,
      //               content: text,
      //             };
      //           }

      //           return message;
      //         },
      //       );

      //       updatedConversation = {
      //         ...updatedConversation,
      //         messages: updatedMessages,
      //       };

      //       setSelectedConversation(updatedConversation);
      //     }
      //   }

      //   saveConversation(updatedConversation);

      //   const updatedConversations: Conversation[] = conversations.map(
      //     (conversation) => {
      //       if (conversation.id === selectedConversation.id) {
      //         return updatedConversation;
      //       }

      //       return conversation;
      //     },
      //   );

      //   if (updatedConversations.length === 0) {
      //     updatedConversations.push(updatedConversation);
      //   }

      //   setConversations(updatedConversations);
      //   saveConversations(updatedConversations);

      //   setMessageIsStreaming(false);
      
    }
  };

  const getUploadedPDFURL_ = async (file:any) => {
    try {
      const filekey = file.sharekey === "" ? file.filekey : file.sharekey;
      const response = await axios.post("/api/aws/s3/download-file", {
        file_key: filekey,
        type: file.type,
        file_name: file.name,
      });
      return response.data.url;
    } catch (error:any) {
      console.error("Error fetching PDF URL:", error.message);
      return null;
    }
  };


  
  // getUploadedPDFURL_(selectedFile).then((url) => {
  //   console.log("Selected FIle : ", selectedFile);
  //   if (url) {
  //     console.log("PDF URL:", url);
  //   } else {
  //     console.log("Failed to get PDF URL");
  //   }
  // });

  useEffect(() => {
    const getPaperDetailsViaAPI = async () => {
      try {
        const pdfURL = await getUploadedPDFURL_(selectedFile); // Assuming getUploadedPDFURL is async
        const selectedFileName = selectedFile?.name;
        console.log("pdfURL: inside", pdfURL);
        console.log("selectedFileName:  inside ", selectedFileName);
        if (!pdfURL || !selectedFileName) {
          console.error("Missing PDF URL or file name");
          return;
        }
  
        const response = await axios.get(
          `http://localhost:8000/api/get_research_paper_details/?pdf_url=${encodeURIComponent(pdfURL)}&filename=${encodeURIComponent(selectedFileName)}`
        );
        const paperDetails = response.data.research_paper_details;
        console.log("Paper details:", paperDetails);
        setPaperDetails(paperDetails);
      } catch (error) {
        console.error("Error fetching paper details:", error);
      }
    };
  
    if (selectedFile?.name) {
      getPaperDetailsViaAPI();
    }
  }, [selectedFile?.name]);


  return (
    <>
      <Head>
        <title>Spyglass AI</title>
        <meta name="description" content="ChatGPT but better." />
        <meta
          name="viewport"
          content="height=device-height ,width=device-width, initial-scale=1, user-scalable=no"
        />
        <link rel="icon" href="/favicon.ico" />
      </Head>
      {selectedConversation && (
        <main
          className={`flex h-screen w-screen flex-col text-sm text-white dark:text-white ${lightMode}`}
        >
            {card.name === "signin" && <Signin />}
            {card.name === "CreateFolder" && <CreateFolder />}
            {card.name === "UploadFile" && <UploadFile />}
            {card.name === "Rename" && <Rename />}
            {card.name === "Delete" && <Delete />}
            {card.name === "Share" && <Share />}
          <div className="fixed top-0 w-full sm:hidden">
            <Navbar
              selectedConversation={selectedConversation}
            />
          </div>

          <div className="flex h-full w-full pt-[48px] sm:pt-0">
            {showSidebar ? (
              <div>
                <Chatbar
                  files={files}
                  folders={folders}
                  loading={messageIsStreaming}
                  conversations={conversations}
                  selectedConversation={selectedConversation}
                />

                <button
                  className="fixed top-5 left-[270px] z-50 h-7 w-7 hover:text-gray-400 dark:text-white dark:hover:text-gray-300 sm:top-0.5 sm:left-[270px] sm:h-8 sm:w-8 sm:text-neutral-700"
                  onClick={handleToggleChatbar}
                >
                  <IconArrowBarLeft />
                </button>
                <div
                  onClick={handleToggleChatbar}
                  className="absolute top-0 left-0 z-10 h-full w-full bg-black opacity-70 sm:hidden"
                ></div>
              </div>
            ) : (
              <button
                className="fixed top-2.5 left-4 z-50 h-7 w-7 text-white hover:text-gray-400 dark:text-white dark:hover:text-gray-300 sm:top-0.5 sm:left-4 sm:h-8 sm:w-8 sm:text-neutral-700"
                onClick={handleToggleChatbar}
              >
                <IconArrowBarRight />
              </button>
            )}

            <div className="flex flex-1">
              <Chat
                conversation={selectedConversation}
                messageIsStreaming={messageIsStreaming}
                onSend={handleSend}
              />
            </div>

            {showPromptbar ? (
              <div>
                {paperDetails && <Promptbar
                  paper={paperDetails}
                />}
                <button
                  className="fixed top-5 right-[270px] z-50 h-7 w-7 hover:text-gray-400 dark:text-white dark:hover:text-gray-300 sm:top-0.5 sm:right-[270px] sm:h-8 sm:w-8 sm:text-neutral-700"
                  onClick={handleTogglePromptbar}
                >
                  <IconArrowBarRight />
                </button>
                <div
                  onClick={handleTogglePromptbar}
                  className="absolute top-0 left-0 z-10 h-full w-full bg-black opacity-70 sm:hidden"
                ></div>
              </div>
            ) : (
              <button
                className="fixed top-2.5 right-4 z-50 h-7 w-7 text-white hover:text-gray-400 dark:text-white dark:hover:text-gray-300 sm:top-0.5 sm:right-4 sm:h-8 sm:w-8 sm:text-neutral-700"
                onClick={handleTogglePromptbar}
              >
                <IconArrowBarLeft />
              </button>
            )}
          </div>
        </main>
      )}
    </>
  );
};
export default Home;