import "./globals.css";

export const metadata = {
  title: "QueryDocs — Ask your documents",
  description: "Upload a document and ask questions grounded in its contents.",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>
        <main>{children}</main>
      </body>
    </html>
  );
}
