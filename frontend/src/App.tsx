import { CardsChat } from "@/components/chat"
import { DocumentsManager } from "@/components/documents"
import { DocumentEmbeddings } from "@/components/embeddings"

function App() {
  return (
    <div className="flex min-h-svh items-center justify-center p-4">
      <div className="w-full max-w-4xl space-y-4">
        <DocumentsManager />
        <CardsChat />
        <DocumentEmbeddings />
      </div>
    </div>
  )
}

export default App