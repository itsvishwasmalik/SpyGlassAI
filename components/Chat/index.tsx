import { Conversation, Message } from '@/types/chat';
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
import { ChatInput } from './ChatInput';
import { ChatLoader } from './ChatLoader';
import { ChatMessage } from './ChatMessage';

interface Props {
  conversation: Conversation;
  messageIsStreaming: boolean;
  loading?: boolean;
  prompts?: any[];
  stopConversationRef?: MutableRefObject<boolean>;
  onSend: (
    message: Message,
    deleteCount?: number,
    plugin?: any
  ) => void;
  onEditMessage?: (message: Message, index: number) => void;
}

export const Chat: FC<Props> = memo(
  ({
    conversation,
    messageIsStreaming,
    loading = false,
    prompts = [],
    stopConversationRef,
    onSend,
    onEditMessage = () => {},
  }) => {
    const { t } = useTranslation('chat');
    const [currentMessage, setCurrentMessage] = useState<Message>();
    const [autoScrollEnabled, setAutoScrollEnabled] = useState<boolean>(true);
    const [showSettings, setShowSettings] = useState<boolean>(false);
    const [showScrollDownButton, setShowScrollDownButton] = useState<boolean>(false);

    const messagesEndRef = useRef<HTMLDivElement>(null);
    const chatContainerRef = useRef<HTMLDivElement>(null);
    const textareaRef = useRef<HTMLTextAreaElement>(null);

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
        <div
          className="max-h-full overflow-x-hidden"
          ref={chatContainerRef}
          onScroll={handleScroll}
        >
          {conversation.messages.length === 0 ? (
            <>
              <div className="mx-auto flex w-[350px] flex-col space-y-10 pt-12 sm:w-[600px]">
                <div className="text-center text-3xl font-semibold text-gray-100">
                  Spyglass AI
                </div>
              </div>
            </>
          ) : (
            <>
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
        //   model={conversation.model}
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
  }
);

Chat.displayName = 'Chat';