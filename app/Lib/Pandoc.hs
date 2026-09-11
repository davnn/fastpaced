{-# LANGUAGE OverloadedStrings #-}

module Lib.Pandoc (articleCompiler) where

import Hakyll
import Text.Pandoc.Options
import Lib.Configuration (citationStyle)
import Lib.Content (articleBibliographies)
import Lib.Metadata (validateArticleMetadata)

-- Additional extensions for pandoc
pandocReaderExtensions :: Extensions
pandocReaderExtensions = extensionsFromList
  [ Ext_mark, Ext_footnotes, Ext_inline_notes, Ext_tex_math_dollars
  , Ext_citations, Ext_fenced_divs
  ]

-- Enhance default ReaderOptions
pandocReaderOptions :: ReaderOptions
pandocReaderOptions = defaultHakyllReaderOptions
  { readerExtensions = readerExtensions defaultHakyllReaderOptions <> pandocReaderExtensions }

-- Enhance default WriterOptions
pandocWriterOptions :: WriterOptions
pandocWriterOptions = defaultHakyllWriterOptions { writerHTMLMathMethod = KaTeX "" }

-- A single bibliography per article is an explicit authoring contract.
-- Load CSL only when citations are actually requested.
articleCompiler :: Compiler (Item String)
articleCompiler = do
  identifier <- getUnderlying
  validateArticleMetadata identifier
  bibliographies <- loadAll (articleBibliographies identifier)
  case bibliographies of
    [] -> pandocCompilerWith pandocReaderOptions pandocWriterOptions
    [bibliography] -> do
      csl <- load citationStyle
      fmap (writePandocWith pandocWriterOptions)
        (getResourceBody >>= readPandocBiblio pandocReaderOptions csl bibliography)
    _ -> fail (toFilePath identifier ++ ": expected at most one .bib file; merge bibliographies before building")
