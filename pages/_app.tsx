import '@/styles/globals.css';
import type { AppProps } from 'next/app';
import { Inter } from 'next/font/google';
import { Toaster } from 'react-hot-toast';
import { SessionProvider } from "next-auth/react";
import { RecoilRoot } from "recoil";
const inter = Inter({ subsets: ['latin'] });


export default function App({ Component, pageProps }: AppProps<{ session: any }>) {
  return (
    <SessionProvider session={pageProps.session}>
      <RecoilRoot>
        <div className={inter.className}>
          <Toaster />
          <Component {...pageProps} />
        </div>
      </RecoilRoot>
    </SessionProvider>
  );
}
