"use client"

import * as React from "react"
import { Trash2, Upload } from "lucide-react"
import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"

interface Document {
  document_id: string
  document_name: string
  document_text?: string
  chunks_added?: number
}

export function DocumentsManager() {
  const [documents, setDocuments] = React.useState<Document[]>([])
  const [isLoading, setIsLoading] = React.useState(false)

  const fetchDocuments = async () => {
    try {
      const response = await fetch("http://localhost:8000/documents")
      if (!response.ok) throw new Error("Failed to fetch documents")
      const data = await response.json()
      setDocuments(data.documents)
    } catch (error) {
      console.error("Error fetching documents:", error)
      alert("Failed to fetch documents")
    }
  }

  React.useEffect(() => {
    fetchDocuments()
  }, [])

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (!file) return

    if (!file.name.endsWith('.docx')) {
      alert("Only .docx files are supported")
      return
    }

    setIsLoading(true)
    const formData = new FormData()
    formData.append("file", file)
    formData.append("document_name", file.name)

    try {
      const response = await fetch("http://localhost:8000/vectorize-document", {
        method: "POST",
        body: formData,
      })

      if (!response.ok) throw new Error("Failed to upload document")
      
      const data = await response.json()
      alert(`Document "${data.document_name}" uploaded successfully`)
      fetchDocuments() // Refresh the list
    } catch (error) {
      console.error("Error uploading document:", error)
      alert("Failed to upload document")
    } finally {
      setIsLoading(false)
    }
  }

  const handleDelete = async (documentId: string) => {
    if (!confirm("Are you sure you want to delete this document?")) return

    try {
      const response = await fetch(`http://localhost:8000/document/${documentId}`, {
        method: "DELETE",
      })

      if (!response.ok) throw new Error("Failed to delete document")
      
      alert("Document deleted successfully")
      fetchDocuments() // Refresh the list
    } catch (error) {
      console.error("Error deleting document:", error)
      alert("Failed to delete document")
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Document Store</CardTitle>
        <CardDescription>
          Upload and manage your company documents
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="mb-4">
          <Button
            disabled={isLoading}
            onClick={() => document.getElementById("file-upload")?.click()}
          >
            <Upload className="mr-2 h-4 w-4" />
            Upload Contract
          </Button>
          <input
            id="file-upload"
            type="file"
            accept=".docx"
            className="hidden"
            onChange={handleFileUpload}
          />
        </div>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Document Name</TableHead>
              <TableHead>Preview</TableHead>
              <TableHead className="w-[100px]">Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {documents.map((doc) => (
              <TableRow key={doc.document_id}>
                <TableCell className="font-medium">{doc.document_name}</TableCell>
                <TableCell className="max-w-[300px] truncate">
                  {doc.document_text || "No preview available"}
                </TableCell>
                <TableCell>
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={() => handleDelete(doc.document_id)}
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </TableCell>
              </TableRow>
            ))}
            {documents.length === 0 && (
              <TableRow>
                <TableCell colSpan={3} className="text-center text-muted-foreground">
                  No documents uploaded yet
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  )
} 