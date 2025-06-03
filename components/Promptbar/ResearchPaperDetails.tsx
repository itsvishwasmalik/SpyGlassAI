import React, { FC } from 'react';
import { IconBook } from '@tabler/icons-react';

interface Reference {
    doi: string | null;
    title: string;
    id: string;
    sourcetitle: string;
}

export interface ResearchPaperDetailsType {
    id: number;
    eid: string;
    doi: string;
    pii: string | null;
    pubmed_id: string | null;
    title: string;
    subtype: string;
    subtypeDescription: string;
    creator: string;
    afid: string | null;
    affilname: string;
    affiliation_city: string;
    affiliation_country: string;
    author_count: number | null;
    author_names: string | null;
    author_ids: string | null;
    author_afids: string | null;
    coverDate: string;
    coverDisplayDate: string;
    publicationName: string;
    issn: string;
    source_id: string;
    eIssn: string;
    aggregationType: string;
    volume: string;
    issueIdentifier: string;
    article_number: string | null;
    pageRange: string;
    description: string | null;
    authkeywords: string | null;
    citedby_count: number;
    openaccess: boolean;
    freetoread: string | null;
    freetoreadLabel: string | null;
    fund_acr: string | null;
    fund_no: string | null;
    fund_sponsor: string | null;
    ref_docs: Reference[];
    created_at: string;
    updated_at: string;
}

interface ResearchPaperDetailsProps {
    details: ResearchPaperDetailsType;
}

export const ResearchPaperDetails: FC<ResearchPaperDetailsProps> = ({ details }) => {
    return (
        <div className="bg-[#202123] flex justify-between flex-col h-full w-full text-white p-4 rounded-md shadow-lg space-y-4">
            <div className="flex items-center gap-2">
                {/* Optional icon */}
                <IconBook size={24} />
                <h2 className="text-xl font-bold">{details.title}</h2>
            </div>

            <table className="min-w-full divide-y text-sm">
                <tbody className="divide-y divide-gray-200">
                    <tr className="">
                        <td className="font-semibold px-4 py-2">DOI:</td>
                        <td className="px-4 py-2">{details.doi}</td>
                    </tr>
                    <tr className="">
                        <td className="font-semibold px-4 py-2">Author:</td>
                        <td className="px-4 py-2">{details.creator}</td>
                    </tr>
                    <tr className="">
                        <td className="font-semibold px-4 py-2">Publication:</td>
                        <td className="px-4 py-2">{details.publicationName}</td>
                    </tr>
                    <tr className="">
                        <td className="font-semibold px-4 py-2">Cover Date:</td>
                        <td className="px-4 py-2">{new Date(details.coverDate).toLocaleDateString()}</td>
                    </tr>
                    <tr className="">
                        <td className="font-semibold px-4 py-2">Volume/Issue:</td>
                        <td className="px-4 py-2">{details.volume} / {details.issueIdentifier}</td>
                    </tr>
                    <tr className="">
                        <td className="font-semibold px-4 py-2">Page Range:</td>
                        <td className="px-4 py-2">{details.pageRange}</td>
                    </tr>
                    <tr className="">
                        <td className="font-semibold px-4 py-2">Affiliation:</td>
                        <td className="px-4 py-2">
                            {details.affilname}, {details.affiliation_city}, {details.affiliation_country}
                        </td>
                    </tr>
                </tbody>
            </table>


            <div>
                <h3 className="text-base font-semibold mb-1">References</h3>
                {details.ref_docs && details.ref_docs.length > 0 ? (
                    <ul className="space-y-2 max-h-60 overflow-auto text-xs">
                        {details.ref_docs.map((ref, idx) => (
                            <li key={idx} className="border-b border-white/20 pb-1">
                                <div className="flex items-center justify-between">
                                    <span>{ref.title}</span>
                                    {ref.doi && (
                                        <a
                                            href={`https://doi.org/${ref.doi}`}
                                            target="_blank"
                                            rel="noreferrer"
                                            className="text-blue-400 hover:underline"
                                        >
                                            [DOI]
                                        </a>
                                    )}
                                </div>
                                <div className="text-gray-400">{ref.sourcetitle}</div>
                            </li>
                        ))}
                    </ul>
                ) : (
                    <p className="text-gray-400">No references available.</p>
                )}
            </div>
        </div>
    );
};
