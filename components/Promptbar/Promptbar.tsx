import { FC } from 'react';
import { ResearchPaperDetails, } from './ResearchPaperDetails';

interface Props {
  paper: any;
}

export const Promptbar: FC<Props> = ({
  paper,
}) => {


  return (
    <div className="fixed top-0 right-0 z-50 flex h-full w-[400px] flex-none flex-col space-y-2 bg-[#202123] p-2 text-[14px] transition-all sm:relative sm:top-0">
      {/* Fixed section to display research paper details */}
      <div className="mt-4 h-full">
        <ResearchPaperDetails details={paper} />
      </div>
    </div>
  );
};
