"use client"

import type React from "react"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Textarea } from "@/components/ui/textarea"
import { useToast } from "@/components/ui/use-toast"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Loader2 } from "lucide-react"

export default function VocabularyImporter() {
  const [theme, setTheme] = useState("")
  const [range, setRange] = useState("1-10")
  const [generatedVocabulary, setGeneratedVocabulary] = useState("")
  const [isLoading, setIsLoading] = useState(false)
  const { toast } = useToast()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    if (!theme.trim()) {
      toast({
        title: "Theme Required",
        description: "Please enter a thematic category.",
        variant: "destructive",
      })
      return
    }

    setIsLoading(true)
    setGeneratedVocabulary("")

    try {
      const response = await fetch("/api/generate-vocabulary", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ theme, range }),
      })

      // Get the response text first
      const responseText = await response.text()

      // Try to parse it as JSON
      let data
      try {
        data = JSON.parse(responseText)
      } catch (parseError) {
        console.error("Error parsing response:", parseError)
        console.log("Response text:", responseText)
        throw new Error(`Invalid JSON response: ${responseText.substring(0, 100)}...`)
      }

      // Check if the response contains an error
      if (!response.ok) {
        throw new Error(data.error || `Server error: ${response.status}`)
      }

      // Check if we have a valid array
      if (!Array.isArray(data)) {
        if (data.error) {
          throw new Error(data.error)
        } else {
          throw new Error("Invalid response format: expected an array of vocabulary words")
        }
      }

      // Format the response as JSON with indentation
      setGeneratedVocabulary(JSON.stringify(data, null, 2))

      toast({
        title: "Success!",
        description: `Generated ${data.length} vocabulary words for theme: "${theme}"`,
      })
    } catch (error) {
      console.error("Error:", error)
      toast({
        title: "Error",
        description: error instanceof Error ? error.message : "Failed to generate vocabulary. Please try again.",
        variant: "destructive",
      })
    } finally {
      setIsLoading(false)
    }
  }

  const copyToClipboard = () => {
    if (!generatedVocabulary) return

    navigator.clipboard
      .writeText(generatedVocabulary)
      .then(() => {
        toast({
          title: "Copied!",
          description: "Vocabulary has been copied to your clipboard.",
        })
      })
      .catch((err) => {
        console.error("Failed to copy:", err)
        toast({
          title: "Copy Failed",
          description: "Could not copy to clipboard. Please try selecting and copying manually.",
          variant: "destructive",
        })
      })
  }

  return (
    <div className="container mx-auto p-4 py-8 max-w-3xl">
      <Card className="mb-8">
        <CardHeader>
          <CardTitle className="text-2xl">Spanish Vocabulary Importer</CardTitle>
          <CardDescription>Generate Spanish vocabulary words based on a thematic category</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <label htmlFor="theme" className="block text-sm font-medium">
                Thematic Category
              </label>
              <Input
                id="theme"
                type="text"
                value={theme}
                onChange={(e) => setTheme(e.target.value)}
                placeholder="Enter a theme (e.g., 'Food', 'Travel', 'Business')"
                className="w-full"
                required
                disabled={isLoading}
              />
            </div>
            <div className="space-y-2">
              <label htmlFor="range" className="block text-sm font-medium">
                Number of Words
              </label>
              <Select value={range} onValueChange={setRange} disabled={isLoading}>
                <SelectTrigger id="range" className="w-full">
                  <SelectValue placeholder="Select range" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="1-10">5-10 words</SelectItem>
                  <SelectItem value="10-50">10-50 words</SelectItem>
                  <SelectItem value="50-100">50-100 words</SelectItem>
                </SelectContent>
              </Select>
              <p className="text-xs text-muted-foreground mt-1">Note: The first option generates 5-10 words minimum.</p>
            </div>
            <Button type="submit" disabled={isLoading} className="w-full">
              {isLoading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Generating...
                </>
              ) : (
                "Generate Vocabulary"
              )}
            </Button>
          </form>
        </CardContent>
      </Card>

      {generatedVocabulary && (
        <Card>
          <CardHeader>
            <CardTitle className="flex justify-between items-center">
              <span>Generated Vocabulary</span>
              <Button onClick={copyToClipboard} variant="outline" size="sm">
                Copy to Clipboard
              </Button>
            </CardTitle>
            <CardDescription>
              JSON output for theme: "{theme}" ({range} words)
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Textarea value={generatedVocabulary} readOnly className="h-[400px] font-mono text-sm" />
          </CardContent>
        </Card>
      )}
    </div>
  )
}

