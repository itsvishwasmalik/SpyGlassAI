import { Conversation, Message } from '@/types/chat';
import { KeyValuePair } from '@/types/data';
import { ErrorMessage } from '@/types/error';
import { OpenAIModel, OpenAIModelID } from '@/types/openai';
import { Prompt } from '@/types/prompt';
import { throttle } from '@/utils';
import { IconArrowDown, IconClearAll, IconSettings } from '@tabler/icons-react';
import { useTranslation } from 'next-i18next';
import {
  FC,
  MutableRefObject,
  memo,
  useCallback,
  useEffect,
  useRef,
  useState,
} from 'react';
import { Spinner } from '../Global/Spinner';
import { ChatInput } from './ChatInput';
import { ChatLoader } from './ChatLoader';
import { ChatMessage } from './ChatMessage';
import { ErrorMessageDiv } from './ErrorMessageDiv';
import { ModelSelect } from './ModelSelect';
import { SystemPrompt } from './SystemPrompt';

interface Props {
  conversation: Conversation;
  models: OpenAIModel[];
  apiKey: string;
  serverSideApiKeyIsSet: boolean;
  defaultModelId: OpenAIModelID;
  messageIsStreaming: boolean;
  modelError: ErrorMessage | null;
  loading: boolean;
  prompts: Prompt[];
  onSend: (
    message: Message,
    deleteCount: number,
    plugin: Plugin | null,
  ) => void;
  onUpdateConversation: (
    conversation: Conversation,
    data: KeyValuePair,
  ) => void;
  onEditMessage: (message: Message, messageIndex: number) => void;
  stopConversationRef: MutableRefObject<boolean>;
}

export const Chat: FC<Props> = memo(
  ({
    conversation,
    models,
    apiKey,
    serverSideApiKeyIsSet,
    defaultModelId,
    messageIsStreaming,
    modelError,
    loading,
    prompts,
    onSend,
    onUpdateConversation,
    onEditMessage,
    stopConversationRef,
  }) => {
    const { t } = useTranslation('chat');
    const [currentMessage, setCurrentMessage] = useState<Message>();
    const [autoScrollEnabled, setAutoScrollEnabled] = useState<boolean>(true);
    const [showSettings, setShowSettings] = useState<boolean>(false);
    const [showScrollDownButton, setShowScrollDownButton] =
      useState<boolean>(false);

    const messagesEndRef = useRef<HTMLDivElement>(null);
    const chatContainerRef = useRef<HTMLDivElement>(null);
    const textareaRef = useRef<HTMLTextAreaElement>(null);

    const scrollToBottom = useCallback(() => {
      if (autoScrollEnabled) {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
        textareaRef.current?.focus();
      }
    }, [autoScrollEnabled]);

    const handleScroll = () => {
      if (chatContainerRef.current) {
        const { scrollTop, scrollHeight, clientHeight } =
          chatContainerRef.current;
        const bottomTolerance = 30;

        if (scrollTop + clientHeight < scrollHeight - bottomTolerance) {
          setAutoScrollEnabled(false);
          setShowScrollDownButton(true);
        } else {
          setAutoScrollEnabled(true);
          setShowScrollDownButton(false);
        }
      }
    };

    const handleScrollDown = () => {
      chatContainerRef.current?.scrollTo({
        top: chatContainerRef.current.scrollHeight,
        behavior: 'smooth',
      });
    };

    const handleSettings = () => {
      setShowSettings(!showSettings);
    };

    const onClearAll = () => {
      if (confirm(t<string>('Are you sure you want to clear all messages?'))) {
        onUpdateConversation(conversation, { key: 'messages', value: [] });
      }
    };

    const scrollDown = () => {
      if (autoScrollEnabled) {
        messagesEndRef.current?.scrollIntoView(true);
      }
    };
    const throttledScrollDown = throttle(scrollDown, 250);

    useEffect(() => {
      throttledScrollDown();
      setCurrentMessage(
        conversation.messages[conversation.messages.length - 2],
      );
    }, [conversation.messages, throttledScrollDown]);

    useEffect(() => {
      const observer = new IntersectionObserver(
        ([entry]) => {
          setAutoScrollEnabled(entry.isIntersecting);
          if (entry.isIntersecting) {
            textareaRef.current?.focus();
          }
        },
        {
          root: null,
          threshold: 0.5,
        },
      );
      const messagesEndElement = messagesEndRef.current;
      if (messagesEndElement) {
        observer.observe(messagesEndElement);
      }
      return () => {
        if (messagesEndElement) {
          observer.unobserve(messagesEndElement);
        }
      };
    }, [messagesEndRef]);

    return (
      <div className="relative flex-1 overflow-hidden bg-[#1e1e1e]">
        {!(apiKey || serverSideApiKeyIsSet) ? (
          <div className="mx-auto flex h-full w-[300px] flex-col justify-center space-y-6 sm:w-[600px]">
            <div className="text-center text-4xl font-bold text-white">
              Welcome to Spyglass AI
            </div>
          </div>
        ) : modelError ? (
          <ErrorMessageDiv error={modelError} />
        ) : (
          <>
            <div
              className="max-h-full overflow-x-hidden"
              ref={chatContainerRef}
              onScroll={handleScroll}
            >
              {conversation.messages.length === 0 ? (
                <>
                  <div className="mx-auto flex w-[350px] flex-col space-y-10 pt-12 sm:w-[600px]">
                    <div className="text-center text-3xl font-semibold text-gray-100">
                      {models.length === 0 ? (
                        <div>
                          <Spinner size="16px" className="mx-auto" />
                        </div>
                      ) : (
                        'Spyglass AI'
                      )}
                    </div>
                  </div>
                </>
              ) : (
                <>
                  <div className="flex justify-center border border-b-neutral-600 bg-[#2e2e2e] py-2 text-sm text-neutral-200">
                    {t('Model')}: {conversation.model.name}
                    <button
                      className="ml-2 cursor-pointer hover:opacity-50"
                      onClick={handleSettings}
                    >
                      <IconSettings size={18} />
                    </button>
                    <button
                      className="ml-2 cursor-pointer hover:opacity-50"
                      onClick={onClearAll}
                    >
                      <IconClearAll size={18} />
                    </button>
                  </div>
                  {showSettings && (
                    <div className="flex flex-col space-y-10 md:mx-auto md:max-w-xl md:gap-6 md:py-3 md:pt-6 lg:max-w-2xl lg:px-0 xl:max-w-3xl">
                      <div className="flex h-full flex-col space-y-4 border-b border-neutral-600 p-4 md:rounded-lg md:border">
                        <ModelSelect
                          model={conversation.model}
                          models={models}
                          defaultModelId={defaultModelId}
                          onModelChange={(model) =>
                            onUpdateConversation(conversation, {
                              key: 'model',
                              value: model,
                            })
                          }
                        />
                      </div>
                    </div>
                  )}

                  {conversation.messages.map((message, index) => (
                    <ChatMessage
                      key={index}
                      message={message}
                      messageIndex={index}
                      onEditMessage={onEditMessage}
                    />
                  ))}

                  {loading && <ChatLoader />}

                  <div
                    className="h-[162px] bg-[#1e1e1e]"
                    ref={messagesEndRef}
                  />
                </>
              )}
            </div>

            <ChatInput
              stopConversationRef={stopConversationRef}
              textareaRef={textareaRef}
              messageIsStreaming={messageIsStreaming}
              conversationIsEmpty={conversation.messages.length === 0}
              model={conversation.model}
              prompts={prompts}
              onSend={(message, plugin) => {
                setCurrentMessage(message);
                onSend(message, 0, plugin);
              }}
              onRegenerate={() => {
                if (currentMessage) {
                  onSend(currentMessage, 2, null);
                }
              }}
            />
          </>
        )}
        {showScrollDownButton && (
          <div className="absolute bottom-0 right-0 mb-4 mr-4 pb-20">
            <button
              className="flex h-7 w-7 items-center justify-center rounded-full bg-gray-700 text-neutral-200 shadow-md hover:shadow-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              onClick={handleScrollDown}
            >
              <IconArrowDown size={18} />
            </button>
          </div>
        )}
      </div>
    );
  },
);
Chat.displayName = 'Chat';
