'use client'

import { useState, useRef } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Upload, Camera, Sparkles, Loader2, MessageSquare } from 'lucide-react'
import { toast } from 'sonner'
import ChatBox from '@/components/ChatBox'

interface PersonaResult {
  name: string
  description: string
  personality: string
  background: string
  traits: string[]
}

interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
}

export default function Home() {
  const [selectedImage, setSelectedImage] = useState<string | null>(null)
  const [persona, setPersona] = useState<PersonaResult | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [isChatLoading, setIsChatLoading] = useState(false)
  const [chatHistory, setChatHistory] = useState<ChatMessage[]>([])
  const fileInputRef = useRef<HTMLInputElement>(null)

  const handleImageUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (file) {
      if (file.type.startsWith('image/')) {
        const reader = new FileReader()
        reader.onload = (e) => {
          setSelectedImage(e.target?.result as string)
          setPersona(null) // Clear previous persona
          setChatHistory([]) // Clear chat history
        }
        reader.readAsDataURL(file)
      } else {
        toast.error('Please select a valid image file')
      }
    }
  }

  const generatePersona = async () => {
    if (!selectedImage) {
      toast.error('Please upload an image first')
      return
    }

    setIsLoading(true)
    try {
      // Convert base64 to blob for upload
      const response = await fetch(selectedImage)
      const blob = await response.blob()
      
      const formData = new FormData()
      formData.append('image', blob, 'uploaded-image.jpg')

      const apiResponse = await fetch('/api/generate-persona', {
        method: 'POST',
        body: formData,
      })

      if (!apiResponse.ok) {
        throw new Error('Failed to generate persona')
      }

      const result = await apiResponse.json()
      setPersona(result.persona)
      setChatHistory([]) // Reset chat history for new persona
      toast.success('Persona generated successfully!')
    } catch (error) {
      console.error('Error generating persona:', error)
      toast.error('Failed to generate persona. Please try again.')
    } finally {
      setIsLoading(false)
    }
  }

  const handleSendMessage = async (message: string) => {
    if (!persona) return

    setIsChatLoading(true)
    try {
      // Optimistically add user message to UI and include it in the request history
      const nextHistory = [
        ...chatHistory,
        { role: 'user' as const, content: message }
      ]
      setChatHistory(nextHistory)

      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message,
          persona,
          chatHistory: nextHistory,
        }),
      })

      if (!response.ok) {
        throw new Error('Failed to get response')
      }

      const result = await response.json()
      
      // Append assistant response
      setChatHistory(prev => [
        ...prev,
        { role: 'assistant', content: result.response }
      ])
    } catch (error) {
      console.error('Error sending message:', error)
      // Show an assistant-style error message
      setChatHistory(prev => [
        ...prev,
        { role: 'assistant', content: "I'm sorry, I'm having trouble responding right now. Please try again." }
      ])
      throw error
    } finally {
      setIsChatLoading(false)
    }
  }

  const triggerFileInput = () => {
    fileInputRef.current?.click()
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 to-pink-50 dark:from-purple-950 dark:to-pink-950">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-900 dark:text-white mb-4">
            Image Persona Generator
          </h1>
          <p className="text-lg text-gray-600 dark:text-gray-300 max-w-2xl mx-auto">
            Upload a photo, generate a persona, and chat with your creation!
          </p>
        </div>

        <div className="grid lg:grid-cols-2 gap-8 max-w-6xl mx-auto mb-8">
          {/* Upload Section */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Camera className="h-5 w-5" />
                Upload Image
              </CardTitle>
              <CardDescription>
                Choose an image containing an object you'd like to give a persona to
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <input
                ref={fileInputRef}
                type="file"
                accept="image/*"
                onChange={handleImageUpload}
                className="hidden"
              />
              
              <div 
                className="border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-lg p-8 text-center cursor-pointer hover:border-purple-500 transition-colors"
                onClick={triggerFileInput}
              >
                {selectedImage ? (
                  <div className="space-y-4">
                    <img
                      src={selectedImage}
                      alt="Uploaded"
                      className="max-w-full max-h-64 mx-auto rounded-lg object-contain"
                    />
                    <p className="text-sm text-gray-500">Click to change image</p>
                  </div>
                ) : (
                  <div className="space-y-4">
                    <Upload className="h-12 w-12 text-gray-400 mx-auto" />
                    <div>
                      <p className="text-lg font-medium text-gray-700 dark:text-gray-300">
                        Drop your image here
                      </p>
                      <p className="text-sm text-gray-500">
                        or click to browse
                      </p>
                    </div>
                  </div>
                )}
              </div>

              <Button 
                onClick={generatePersona}
                disabled={!selectedImage || isLoading}
                className="w-full"
                size="lg"
              >
                {isLoading ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Generating Persona...
                  </>
                ) : (
                  <>
                    <Sparkles className="mr-2 h-4 w-4" />
                    Generate Persona
                  </>
                )}
              </Button>
            </CardContent>
          </Card>

          {/* Persona & Chat Section */}
          <Card>
            <Tabs defaultValue="persona">
              <CardHeader className="pb-0">
                <TabsList className="grid w-full grid-cols-2">
                  <TabsTrigger value="persona" className="flex items-center gap-2">
                    <Sparkles className="h-4 w-4" />
                    Persona
                  </TabsTrigger>
                  <TabsTrigger value="chat" className="flex items-center gap-2" disabled={!persona}>
                    <MessageSquare className="h-4 w-4" />
                    Chat
                  </TabsTrigger>
                </TabsList>
              </CardHeader>
              
              <CardContent className="p-0">
                <TabsContent value="persona" className="mt-0">
                  <div className="p-6">
                    {persona ? (
                      <div className="space-y-6">
                        <div>
                          <h3 className="text-xl font-semibold text-purple-700 dark:text-purple-400 mb-2">
                            {persona.name}
                          </h3>
                          <p className="text-gray-600 dark:text-gray-300">
                            {persona.description}
                          </p>
                        </div>

                        <div>
                          <h4 className="font-medium text-gray-900 dark:text-white mb-2">
                            Personality
                          </h4>
                          <p className="text-gray-600 dark:text-gray-300">
                            {persona.personality}
                          </p>
                        </div>

                        <div>
                          <h4 className="font-medium text-gray-900 dark:text-white mb-2">
                            Background Story
                          </h4>
                          <p className="text-gray-600 dark:text-gray-300">
                            {persona.background}
                          </p>
                        </div>

                        <div>
                          <h4 className="font-medium text-gray-900 dark:text-white mb-3">
                            Key Traits
                          </h4>
                          <div className="flex flex-wrap gap-2">
                            {persona.traits.map((trait, index) => (
                              <span
                                key={index}
                                className="px-3 py-1 bg-purple-100 dark:bg-purple-900 text-purple-700 dark:text-purple-300 rounded-full text-sm"
                              >
                                {trait}
                              </span>
                            ))}
                          </div>
                        </div>
                      </div>
                    ) : (
                      <div className="text-center py-12">
                        <Sparkles className="h-16 w-16 text-gray-300 mx-auto mb-4" />
                        <p className="text-gray-500">
                          Upload an image and click "Generate Persona" to see the magic happen!
                        </p>
                      </div>
                    )}
                  </div>
                </TabsContent>
                
                <TabsContent value="chat" className="mt-0">
                  <ChatBox
                    persona={persona}
                    onSendMessage={handleSendMessage}
                    chatHistory={chatHistory}
                    isLoading={isChatLoading}
                  />
                </TabsContent>
              </CardContent>
            </Tabs>
          </Card>
        </div>

        {/* Instructions */}
        <Card className="max-w-4xl mx-auto">
          <CardHeader>
            <CardTitle>How It Works</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid md:grid-cols-4 gap-6">
              <div className="text-center">
                <div className="w-12 h-12 bg-purple-100 dark:bg-purple-900 rounded-full flex items-center justify-center mx-auto mb-3">
                  <Upload className="h-6 w-6 text-purple-600 dark:text-purple-400" />
                </div>
                <h3 className="font-medium mb-2">1. Upload Image</h3>
                <p className="text-sm text-gray-600 dark:text-gray-300">
                  Choose any image containing an object, person, or scene
                </p>
              </div>
              <div className="text-center">
                <div className="w-12 h-12 bg-purple-100 dark:bg-purple-900 rounded-full flex items-center justify-center mx-auto mb-3">
                  <Sparkles className="h-6 w-6 text-purple-600 dark:text-purple-400" />
                </div>
                <h3 className="font-medium mb-2">2. Generate Persona</h3>
                <p className="text-sm text-gray-600 dark:text-gray-300">
                  AI analyzes the image and creates a unique personality
                </p>
              </div>
              <div className="text-center">
                <div className="w-12 h-12 bg-purple-100 dark:bg-purple-900 rounded-full flex items-center justify-center mx-auto mb-3">
                  <MessageSquare className="h-6 w-6 text-purple-600 dark:text-purple-400" />
                </div>
                <h3 className="font-medium mb-2">3. Chat & Interact</h3>
                <p className="text-sm text-gray-600 dark:text-gray-300">
                  Have conversations with your newly created persona
                </p>
              </div>
              <div className="text-center">
                <div className="w-12 h-12 bg-purple-100 dark:bg-purple-900 rounded-full flex items-center justify-center mx-auto mb-3">
                  <Camera className="h-6 w-6 text-purple-600 dark:text-purple-400" />
                </div>
                <h3 className="font-medium mb-2">4. Explore Stories</h3>
                <p className="text-sm text-gray-600 dark:text-gray-300">
                  Discover their background, personality, and unique traits
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}