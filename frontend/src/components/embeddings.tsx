"use client"

import * as React from "react"
import { Search } from "lucide-react"
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
import { Input } from "@/components/ui/input"
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip"

interface EmbeddingResult {
  text: string
  document_id: string
  document_name: string
  section: string | null
  score: number
}

function trimText(text: string, maxLength = 80) {
  if (text.length <= maxLength) return text
  return text.slice(0, maxLength) + "..."
}

export function DocumentEmbeddings() {
  const [query, setQuery] = React.useState("")
  const [results, setResults] = React.useState<EmbeddingResult[]>([])
  const [isLoading, setIsLoading] = React.useState(false)

  const searchEmbeddings = async () => {
    if (!query.trim()) return

    try {
      setIsLoading(true)
      const response = await fetch("http://localhost:8000/embeddings", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ query: query.trim(), limit: 5 }),
      })

      if (!response.ok) throw new Error("Failed to get embeddings")
      
      const data = await response.json()
      setResults(data.results)
    } catch (error) {
      console.error("Error searching embeddings:", error)
      setResults([])
    } finally {
      setIsLoading(false)
    }
  }

  // Sort results so that any row with 'Place of Work Your' in text (case-insensitive) is last
  const sortedResults = [
    ...results.filter(r => !r.text.toLowerCase().includes("place of work your")),
    ...results.filter(r => r.text.toLowerCase().includes("place of work your")),
  ]

  return (
    <Card>
      <CardHeader>
        <CardTitle>Document Embeddings</CardTitle>
        <CardDescription>
          Search for similar document sections using semantic search
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="flex gap-2 mb-4">
          <Input
            placeholder="Enter search query..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && searchEmbeddings()}
          />
          <Button onClick={searchEmbeddings} disabled={isLoading}>
            <Search className="mr-2 h-4 w-4" />
            Search
          </Button>
        </div>
        <Table className="table-fixed">
          <TableHeader>
            <TableRow>
              <TableHead className="w-[40%]">Document</TableHead>
              <TableHead className="w-[40%]">Text</TableHead>
              <TableHead className="w-[20%] text-right">Score</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {sortedResults.map((result, index) => (
              <TableRow key={`${result.document_id}-${index}`}>
                <TableCell className="w-[40%] truncate overflow-hidden whitespace-nowrap">{result.document_name}</TableCell>
                <TableCell className="w-[40%] truncate overflow-hidden whitespace-nowrap">
                  <TooltipProvider>
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <div>{trimText(result.text)}</div>
                      </TooltipTrigger>
                      <TooltipContent side="top" align="start" className="max-w-[500px]">
                        <p className="whitespace-pre-wrap">{result.text}</p>
                      </TooltipContent>
                    </Tooltip>
                  </TooltipProvider>
                </TableCell>
                <TableCell className="w-[20%] text-right truncate overflow-hidden whitespace-nowrap">
                  {result.score.toFixed(2)}
                </TableCell>
              </TableRow>
            ))}
            {results.length === 0 && !isLoading && (
              <TableRow>
                <TableCell colSpan={3} className="text-center text-muted-foreground">
                  No results found
                </TableCell>
              </TableRow>
            )}
            {isLoading && (
              <TableRow>
                <TableCell colSpan={3} className="text-center text-muted-foreground">
                  Searching...
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  )
} 