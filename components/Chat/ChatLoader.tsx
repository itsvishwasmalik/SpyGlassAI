import { IconRobot, IconDots } from '@tabler/icons-react';
import { FC } from 'react';

interface Props {}

export const ChatLoader: FC<Props> = () => {
  return (
    <div className="flex flex-col">
      <div
        className="
          max-w-[80%]
          self-start
          bg-[#444654]
          text-gray-100
          rounded-xl
          p-4
          my-2
          shadow-sm
          flex
          items-center
          space-x-3
          relative
        "
      >
        {/* Bot icon on the left, just like assistant messages */}
        <div className="absolute -left-10 top-3">
          <IconRobot size={28} className="text-gray-300" />
        </div>

        {/* Three‐dot loading indicator */}
        <IconDots className="animate-pulse" size={28} />
      </div>
    </div>
  );
};
