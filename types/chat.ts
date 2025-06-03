
export interface Message {
  role: Role;
  content: string;
}

export type Role = 'assistant' | 'user';

export interface Conversation {
  id: string;
  name: string;
  messages: Message[];
  doi: string;
  createdAt: string;
}
