import '@/styles/globals.css';
import { appWithTranslation } from 'next-i18next';
import type { AppProps } from 'next/app';
import { Inter } from 'next/font/google';
import { Toaster } from 'react-hot-toast';
import { SessionProvider } from "next-auth/react";
import { RecoilRoot } from "recoil";
const inter = Inter({ subsets: ['latin'] });

interface CustomPageProps {
  session?: any;
}

function App({ Component, pageProps }: AppProps<CustomPageProps>) {
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

export default appWithTranslation(App);
