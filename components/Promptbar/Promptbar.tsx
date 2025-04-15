import { Folder } from '@/types/folder';
import { Prompt } from '@/types/prompt';
import {
  IconFolderPlus,
  IconMistOff,
  IconPlus,
} from '@tabler/icons-react';
import { FC, useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Search } from '../Sidebar/Search';
import { PromptbarSettings } from './PromptbarSettings';
import { Prompts } from './Prompts';
import { ResearchPaperDetails, ResearchPaperDetailsType } from './ResearchPaperDetails';

interface Props {
  prompts: Prompt[];
  paper: any;
  onCreatePrompt: () => void;
  onUpdatePrompt: (prompt: Prompt) => void;
  onDeletePrompt: (prompt: Prompt) => void;
}

export const Promptbar: FC<Props> = ({
  prompts,
  paper,
  onCreatePrompt,
  onUpdatePrompt,
  onDeletePrompt,
}) => {

  const { t } = useTranslation('promptbar');
  const [searchTerm, setSearchTerm] = useState<string>('');
  const [filteredPrompts, setFilteredPrompts] = useState<Prompt[]>(prompts);


  return (
    <div className="fixed top-0 right-0 z-50 flex h-full w-[400px] flex-none flex-col space-y-2 bg-[#202123] p-2 text-[14px] transition-all sm:relative sm:top-0">
      {/* Fixed section to display research paper details */}
      <div className="mt-4 h-full">
        <ResearchPaperDetails details={paper} />
      </div>

      <PromptbarSettings />
    </div>
  );
};
