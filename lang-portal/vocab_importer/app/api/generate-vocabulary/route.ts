import { NextResponse } from "next/server"
import OpenAI from "openai"

// Set a longer timeout for the API route
export const maxDuration = 60

const openai = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY,
})

export async function POST(req: Request) {
  try {
    // Parse the request body
    const body = await req.json().catch(() => null)

    if (!body || !body.theme) {
      return NextResponse.json({ error: "Theme is required" }, { status: 400 })
    }

    const { theme, range } = body

    // Validate theme
    if (typeof theme !== "string" || !theme.trim()) {
      return NextResponse.json({ error: "Theme must be a non-empty string" }, { status: 400 })
    }

    // Determine word count range
    let minWords, maxWords
    switch (range) {
      case "1-10":
        minWords = 5
        maxWords = 10
        break
      case "10-50":
        minWords = 10
        maxWords = 50
        break
      case "50-100":
        minWords = 50
        maxWords = 100
        break
      default:
        return NextResponse.json({ error: "Invalid range. Must be one of: 1-10, 10-50, 50-100" }, { status: 400 })
    }

    // Create the prompt for OpenAI
    const prompt = `Generate a list of ${minWords} to ${maxWords} Spanish vocabulary words related to the theme "${theme}". 
    
    For each word, provide:
    1. The Spanish word
    2. Its English translation
    3. A pronunciation guide written phonetically for English speakers
    
    Format the response as a valid JSON array with the following structure:
    [
      {
        "spanish": "word in Spanish",
        "english": "English translation",
        "pronunciation": "pronunciation guide"
      }
    ]
    
    Ensure:
    - The pronunciation guide uses capital letters for stressed syllables
    - All JSON is properly formatted and valid
    - Each word is relevant to the theme "${theme}"
    - Include exactly between ${minWords} and ${maxWords} words
    - IMPORTANT: Return ONLY the JSON array with no additional text or explanation`

    // Call OpenAI API
    try {
      const completion = await openai.chat.completions.create({
        model: "gpt-3.5-turbo",
        messages: [{ role: "user", content: prompt }],
        temperature: 0.7,
        response_format: { type: "json_object" },
      })

      // Get the response content
      const generatedContent = completion.choices[0].message.content?.trim() || '{"words": []}'

      try {
        // Parse the JSON response
        const parsedContent = JSON.parse(generatedContent)

        // Extract the words array if it exists, otherwise use the whole object
        const vocabularyList = Array.isArray(parsedContent)
          ? parsedContent
          : parsedContent.words || parsedContent.vocabulary || []

        // Validate the structure of each item
        const validatedList = Array.isArray(vocabularyList)
          ? vocabularyList.map((item: any) => ({
              spanish: item.spanish || "",
              english: item.english || "",
              pronunciation: item.pronunciation || "",
            }))
          : []

        return NextResponse.json(validatedList)
      } catch (parseError) {
        console.error("JSON Parse Error:", parseError)
        console.log("Generated content:", generatedContent)

        // Return a valid JSON response even when parsing fails
        return NextResponse.json(
          { error: "Failed to parse generated vocabulary", details: String(parseError) },
          { status: 500 },
        )
      }
    } catch (openaiError) {
      console.error("OpenAI API Error:", openaiError)

      // Return a valid JSON response for OpenAI API errors
      return NextResponse.json({ error: "Error calling OpenAI API", details: String(openaiError) }, { status: 500 })
    }
  } catch (error) {
    console.error("General Error:", error)

    // Return a valid JSON response for any other errors
    return NextResponse.json({ error: "Failed to generate vocabulary", details: String(error) }, { status: 500 })
  }
}

