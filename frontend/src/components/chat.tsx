"use client"

import * as React from "react"
import { ArrowUpIcon, CheckIcon, PlusIcon } from "lucide-react"

import { cn } from "@/lib/utils"
import {
  Avatar,
  AvatarFallback,
  AvatarImage,
} from "@/components/ui/avatar"
import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardFooter,
  CardHeader,
} from "@/components/ui/card"
import {
  Command,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
} from "@/components/ui/command"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip"

const users = [
  {
    name: "Olivia Martin",
    email: "m@example.com",
    avatar: "/avatars/01.png",
  },
  {
    name: "Isabella Nguyen",
    email: "isabella.nguyen@email.com",
    avatar: "/avatars/03.png",
  },
  {
    name: "Emma Wilson",
    email: "emma@example.com",
    avatar: "/avatars/05.png",
  },
  {
    name: "Jackson Lee",
    email: "lee@example.com",
    avatar: "/avatars/02.png",
  },
  {
    name: "William Kim",
    email: "will@email.com",
    avatar: "/avatars/04.png",
  },
] as const

type User = (typeof users)[number]

// Update the formatMessage function to handle lists and line breaks
const formatMessage = (content: string) => {
  // Split by newlines to handle each line
  const lines = content.split(/\n/);
  
  return lines.map((line, index) => {
    // Check if this is a numbered list item
    const listMatch = line.match(/^(\d+)\.\s+(.+)$/);
    if (listMatch) {
      return (
        <div key={index} className="flex gap-2">
          <span className="font-medium">{listMatch[1]}.</span>
          <span>{formatBoldText(listMatch[2])}</span>
        </div>
      );
    }
    
    // Handle regular text with bold formatting
    return <div key={index}>{formatBoldText(line)}</div>;
  });
};

// Helper function to format bold text
const formatBoldText = (text: string) => {
  const parts = text.split(/(\*\*.*?\*\*)/g);
  return parts.map((part, index) => {
    if (part.startsWith('**') && part.endsWith('**')) {
      return <strong key={index}>{part.slice(2, -2)}</strong>;
    }
    return part;
  });
};

export function CardsChat() {
  const [open, setOpen] = React.useState(false)
  const [selectedUsers, setSelectedUsers] = React.useState<User[]>([])
  const [isLoading, setIsLoading] = React.useState(false)

  const [messages, setMessages] = React.useState([
    {
      role: "agent",
      content: "Hi, how can I help you today?",
    },
  ])
  const [input, setInput] = React.useState("")
  const inputLength = input.trim().length

  const sendMessage = async (content: string) => {
    try {
      setIsLoading(true)
      // Add user message immediately
      setMessages(prev => [...prev, { role: "user", content }])
      
      // Make API call
      const response = await fetch("http://localhost:8000/query", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ query: content }),
      })

      if (!response.ok) {
        throw new Error("Failed to get response")
      }

      const data = await response.json()
      
      // Add AI response
      setMessages(prev => [...prev, { role: "agent", content: data.result }])
    } catch (error) {
      console.error("Error sending message:", error)
      // Add error message
      setMessages(prev => [...prev, { 
        role: "agent", 
        content: "I apologize, but I'm having trouble processing your request. Please try again." 
      }])
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <>
      <Card>
        <CardHeader className="flex flex-row items-center">
          <div className="flex items-center gap-4">
            <Avatar className="border">
              <AvatarImage src="/avatars/01.png" alt="Image" />
              <AvatarFallback>E</AvatarFallback>
            </Avatar>
            <div className="flex flex-col gap-0.5">
              <p className="text-sm leading-none font-medium">AI Assistant</p>
              <p className="text-muted-foreground text-xs">Ask me anything</p>
            </div>
          </div>
          <TooltipProvider delayDuration={0}>
            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  size="icon"
                  variant="secondary"
                  className="ml-auto size-8 rounded-full"
                  onClick={() => setOpen(true)}
                >
                  <PlusIcon />
                  <span className="sr-only">New message</span>
                </Button>
              </TooltipTrigger>
              <TooltipContent sideOffset={10}>New message</TooltipContent>
            </Tooltip>
          </TooltipProvider>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col gap-4">
            {messages.map((message, index) => (
              <div
                key={index}
                className={cn(
                  "flex w-max max-w-[75%] flex-col gap-2 rounded-lg px-3 py-2 text-sm",
                  message.role === "user"
                    ? "bg-primary text-primary-foreground ml-auto"
                    : "bg-muted"
                )}
              >
                {formatMessage(message.content)}
              </div>
            ))}
            {isLoading && (
              <div className="flex w-max max-w-[75%] flex-col gap-2 rounded-lg px-3 py-2 text-sm bg-muted">
                Thinking...
              </div>
            )}
          </div>
        </CardContent>
        <CardFooter>
          <form
            onSubmit={(event: React.FormEvent<HTMLFormElement>) => {
              event.preventDefault()
              if (inputLength === 0 || isLoading) return
              sendMessage(input)
              setInput("")
            }}
            className="relative w-full"
          >
            <Input
              id="message"
              placeholder="Type your message..."
              className="flex-1 pr-10"
              autoComplete="off"
              value={input}
              onChange={(event) => setInput(event.target.value)}
              disabled={isLoading}
            />
            <Button
              type="submit"
              size="icon"
              className="absolute top-1/2 right-2 size-6 -translate-y-1/2 rounded-full"
              disabled={inputLength === 0 || isLoading}
            >
              <ArrowUpIcon className="size-3.5" />
              <span className="sr-only">Send</span>
            </Button>
          </form>
        </CardFooter>
      </Card>
      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent className="gap-0 p-0 outline-none">
          <DialogHeader className="px-4 pt-5 pb-4">
            <DialogTitle>New message</DialogTitle>
            <DialogDescription>
              Invite a user to this thread. This will create a new group
              message.
            </DialogDescription>
          </DialogHeader>
          <Command className="overflow-hidden rounded-t-none border-t bg-transparent">
            <CommandInput placeholder="Search user..." />
            <CommandList>
              <CommandEmpty>No users found.</CommandEmpty>
              <CommandGroup>
                {users.map((user) => (
                  <CommandItem
                    key={user.email}
                    data-active={selectedUsers.includes(user)}
                    className="data-[active=true]:opacity-50"
                    onSelect={() => {
                      if (selectedUsers.includes(user)) {
                        return setSelectedUsers(
                          selectedUsers.filter(
                            (selectedUser) => selectedUser !== user
                          )
                        )
                      }

                      return setSelectedUsers(
                        [...users].filter((u) =>
                          [...selectedUsers, user].includes(u)
                        )
                      )
                    }}
                  >
                    <Avatar className="border">
                      <AvatarImage src={user.avatar} alt="Image" />
                      <AvatarFallback>{user.name[0]}</AvatarFallback>
                    </Avatar>
                    <div className="ml-2">
                      <p className="text-sm leading-none font-medium">
                        {user.name}
                      </p>
                      <p className="text-muted-foreground text-sm">
                        {user.email}
                      </p>
                    </div>
                    {selectedUsers.includes(user) ? (
                      <CheckIcon className="text-primary ml-auto flex size-4" />
                    ) : null}
                  </CommandItem>
                ))}
              </CommandGroup>
            </CommandList>
          </Command>
          <DialogFooter className="flex items-center border-t p-4 sm:justify-between">
            {selectedUsers.length > 0 ? (
              <div className="flex -space-x-2 overflow-hidden">
                {selectedUsers.map((user) => (
                  <Avatar key={user.email} className="inline-block border">
                    <AvatarImage src={user.avatar} />
                    <AvatarFallback>{user.name[0]}</AvatarFallback>
                  </Avatar>
                ))}
              </div>
            ) : (
              <p className="text-muted-foreground text-sm">
                Select users to add to this thread.
              </p>
            )}
            <Button
              disabled={selectedUsers.length < 2}
              size="sm"
              onClick={() => {
                setOpen(false)
              }}
            >
              Continue
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  )
} 