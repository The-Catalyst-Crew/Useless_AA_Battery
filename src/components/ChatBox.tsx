'use client'

import { useState, useRef, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Send, MessageSquare, Bot, User } from 'lucide-react'

interface ChatMessage {
  id: string
  text: string
  sender: 'user' | 'persona'
  timestamp: Date
}

interface PersonaData {
  name: string
  description: string
  personality: string
  background: string
  traits: string[]
}

interface ChatBoxProps {
  persona: PersonaData | null
  onSendMessage: (message: string) => Promise<void>
  chatHistory: Array<{ role: 'user' | 'assistant'; content: string }>
  isLoading?: boolean
}

export default function ChatBox({ persona, onSendMessage, chatHistory, isLoading = false }: ChatBoxProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [inputMessage, setInputMessage] = useState('')
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  // Sync rendered messages with external chat history from parent
  useEffect(() => {
    const mapped: ChatMessage[] = chatHistory.map((m, idx) => ({
      id: `${Date.now()}-${idx}`,
      text: m.content,
      sender: m.role === 'user' ? 'user' : 'persona',
      timestamp: new Date()
    }))
    setMessages(mapped)
  }, [chatHistory])

  const handleSendMessage = async () => {
    if (!inputMessage.trim() || !persona || isLoading) return
    const messageToSend = inputMessage
    setInputMessage('')

    try {
      await onSendMessage(messageToSend)
    } catch (error) {
      console.error('Error sending message:', error)
      // Show error bubble locally
      const errorMessage: ChatMessage = {
        id: Date.now().toString(),
        text: "I'm sorry, I'm having trouble responding right now. Please try again.",
        sender: 'persona',
        timestamp: new Date()
      }
      setMessages(prev => [...prev, errorMessage])
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSendMessage()
    }
  }

  if (!persona) {
    return (
      <Card>
        <CardContent className="flex items-center justify-center h-full p-6">
          <div className="text-center text-gray-500">
            <MessageSquare className="h-12 w-12 mx-auto mb-4 opacity-50" />
            <p>Generate a persona first to start chatting!</p>
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card className="flex flex-col">
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center gap-2">
          <MessageSquare className="h-5 w-5" />
          Chat with {persona.name}
        </CardTitle>
      </CardHeader>
      
      <CardContent className="flex flex-col p-0">
        <div className="px-4 py-3">
          <div className="space-y-4">
            {messages.map((message) => (
              <div
                key={message.id}
                className={`flex gap-3 ${
                  message.sender === 'user' ? 'justify-end' : 'justify-start'
                }`}
              >
                {message.sender === 'persona' && (
                  <div className="flex-shrink-0">
                    <div className="w-8 h-8 bg-purple-100 dark:bg-purple-900 rounded-full flex items-center justify-center">
                      <Bot className="h-4 w-4 text-purple-600 dark:text-purple-400" />
                    </div>
                  </div>
                )}
                
                <div
                  className={`max-w-[80%] rounded-lg px-4 py-2 ${
                    message.sender === 'user'
                      ? 'bg-blue-500 text-white'
                      : 'bg-gray-100 dark:bg-gray-800 text-gray-900 dark:text-gray-100'
                  }`}
                >
                  <p className="text-sm whitespace-pre-wrap">{message.text}</p>
                  <p className="text-xs opacity-70 mt-1">
                    {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </p>
                </div>
                
                {message.sender === 'user' && (
                  <div className="flex-shrink-0">
                    <div className="w-8 h-8 bg-blue-100 dark:bg-blue-900 rounded-full flex items-center justify-center">
                      <User className="h-4 w-4 text-blue-600 dark:text-blue-400" />
                    </div>
                  </div>
                )}
              </div>
            ))}
            
            {isLoading && (
              <div className="flex gap-3 justify-start">
                <div className="flex-shrink-0">
                  <div className="w-8 h-8 bg-purple-100 dark:bg-purple-900 rounded-full flex items-center justify-center">
                    <Bot className="h-4 w-4 text-purple-600 dark:text-purple-400" />
                  </div>
                </div>
                <div className="bg-gray-100 dark:bg-gray-800 rounded-lg px-4 py-2">
                  <div className="flex gap-1">
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                  </div>
                </div>
              </div>
            )}
            
            <div ref={messagesEndRef} />
          </div>
        </div>
        
        <div className="p-4 border-t">
          <div className="flex gap-2">
            <Input
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder={`Message ${persona.name}...`}
              disabled={isLoading}
              className="flex-1"
            />
            <Button
              onClick={handleSendMessage}
              disabled={!inputMessage.trim() || isLoading}
              size="icon"
            >
              <Send className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}