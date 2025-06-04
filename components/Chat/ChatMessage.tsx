import { Message } from '@/types/chat';
import { IconCheck, IconCopy, IconEdit, IconRobot } from '@tabler/icons-react';
import { useTranslation } from 'next-i18next';
import { FC, memo, useEffect, useRef, useState } from 'react';
import rehypeMathjax from 'rehype-mathjax';
import remarkGfm from 'remark-gfm';
import remarkMath from 'remark-math';
import { CodeBlock } from '../Markdown/CodeBlock';
import { MemoizedReactMarkdown } from '../Markdown/MemoizedReactMarkdown';

interface Props {
  message: Message;
  messageIndex: number;
  onEditMessage: (message: Message, messageIndex: number) => void;
}

export const ChatMessage: FC<Props> = memo(
  ({ message, messageIndex, onEditMessage }) => {
    const { t } = useTranslation('chat');
    const [isEditing, setIsEditing] = useState<boolean>(false);
    const [isTyping, setIsTyping] = useState<boolean>(false);
    const [messageContent, setMessageContent] = useState(message.content);
    const [messagedCopied, setMessageCopied] = useState(false);

    const textareaRef = useRef<HTMLTextAreaElement>(null);

    const toggleEditing = () => {
      setIsEditing(!isEditing);
    };

    const handleInputChange = (
      event: React.ChangeEvent<HTMLTextAreaElement>,
    ) => {
      setMessageContent(event.target.value);
      if (textareaRef.current) {
        textareaRef.current.style.height = 'inherit';
        textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`;
      }
    };

    const handleEditMessage = () => {
      if (message.content !== messageContent) {
        onEditMessage({ ...message, content: messageContent }, messageIndex);
      }
      setIsEditing(false);
    };

    const handlePressEnter = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
      if (e.key === 'Enter' && !isTyping && !e.shiftKey) {
        e.preventDefault();
        handleEditMessage();
      }
    };

    const copyOnClick = () => {
      if (!navigator.clipboard) return;

      navigator.clipboard.writeText(message.content).then(() => {
        setMessageCopied(true);
        setTimeout(() => {
          setMessageCopied(false);
        }, 2000);
      });
    };

    useEffect(() => {
      if (textareaRef.current) {
        textareaRef.current.style.height = 'inherit';
        textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`;
      }
    }, [isEditing]);

    //
    // Determine bubble‐style classes:
    //
    const isAssistant = message.role === 'assistant';
    const bubbleBase =
      'max-w-[80%] whitespace-pre-wrap break-words text-base md:text-lg leading-snug';
    const assistantClasses = [
      'self-start',
      'bg-[#444654]',
      'text-gray-100',
      'rounded-xl',
      'p-4',
      'my-2',
      'shadow-sm',
    ].join(' ');
    const userClasses = [
      'self-end',
      'bg-[#1F2937]', // slightly lighter than page bg
      'text-gray-200',
      'rounded-xl',
      'p-4',
      'my-2',
      'shadow-sm',
    ].join(' ');

    return (
      <div className="flex flex-col group">
        <div
          className={`${bubbleBase} ${
            isAssistant ? assistantClasses : userClasses
          } flex flex-col relative`}
        >
          {/* 
            ChatGPT only shows the bot icon on assistant messages.
            We completely hide the user icon for user messages.
          */}
          {isAssistant && (
            <div className="absolute -left-10 top-2">
              {/* Replace this with your own ChatGPT‐style bot SVG if desired */}
              <IconRobot size={28} className="text-gray-300" />
            </div>
          )}

          <div className="flex flex-col">
            {message.role === 'user' ? (
              <>
                {isEditing ? (
                  <div className="flex flex-col">
                    <textarea
                      ref={textareaRef}
                      className="w-full resize-none bg-transparent text-inherit focus:outline-none"
                      value={messageContent}
                      onChange={handleInputChange}
                      onKeyDown={handlePressEnter}
                      onCompositionStart={() => setIsTyping(true)}
                      onCompositionEnd={() => setIsTyping(false)}
                      style={{
                        fontFamily: 'inherit',
                        fontSize: 'inherit',
                        lineHeight: 'inherit',
                        padding: '0',
                        margin: '0',
                        overflow: 'hidden',
                      }}
                    />
                    <div className="mt-4 flex justify-end space-x-2">
                      <button
                        className="h-8 rounded-md bg-blue-600 px-3 py-1 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
                        onClick={handleEditMessage}
                        disabled={messageContent.trim().length <= 0}
                      >
                        {t('Save')}
                      </button>
                      <button
                        className="h-8 rounded-md border border-gray-500 px-3 py-1 text-sm text-gray-300 hover:bg-gray-700"
                        onClick={() => {
                          setMessageContent(message.content);
                          setIsEditing(false);
                        }}
                      >
                        {t('Cancel')}
                      </button>
                    </div>
                  </div>
                ) : (
                  <div className="prose prose-invert">{message.content}</div>
                )}

                {/* Edit icon */}
                {!isEditing && (
                  <button
                    onClick={toggleEditing}
                    className="absolute top-2 right-2 text-gray-400 opacity-0 group-hover:opacity-100 hover:text-gray-200 transition-opacity"
                  >
                    <IconEdit size={18} />
                  </button>
                )}
              </>
            ) : (
              <>
                <MemoizedReactMarkdown
                  className="prose prose-invert"
                  remarkPlugins={[remarkGfm, remarkMath]}
                  rehypePlugins={[rehypeMathjax]}
                  components={{
                    code({ node, inline, className, children, ...props }) {
                      const match = /language-(\w+)/.exec(className || '');
                      return !inline && match ? (
                        <CodeBlock
                          key={Math.random()}
                          language={match[1]}
                          value={String(children).replace(/\n$/, '')}
                          {...props}
                        />
                      ) : (
                        <code className={className} {...props}>
                          {children}
                        </code>
                      );
                    },
                    table({ children }) {
                      return (
                        <table className="border-collapse border border-gray-600 py-1 px-3">
                          {children}
                        </table>
                      );
                    },
                    th({ children }) {
                      return (
                        <th className="break-words border border-gray-600 bg-gray-800 py-1 px-3 text-gray-100">
                          {children}
                        </th>
                      );
                    },
                    td({ children }) {
                      return (
                        <td className="break-words border border-gray-600 py-1 px-3">
                          {children}
                        </td>
                      );
                    },
                  }}
                >
                  {message.content}
                </MemoizedReactMarkdown>

                {/* Copy icon */}
                <div className="absolute top-2 right-2 flex items-center">
                  {messagedCopied ? (
                    <IconCheck size={18} className="text-green-400" />
                  ) : (
                    <button
                      onClick={copyOnClick}
                      className="text-gray-400 opacity-0 group-hover:opacity-100 hover:text-gray-200 transition-opacity"
                    >
                      <IconCopy size={18} />
                    </button>
                  )}
                </div>
              </>
            )}
          </div>
        </div>
      </div>
    );
  },
);
ChatMessage.displayName = 'ChatMessage';
