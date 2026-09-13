{-# LANGUAGE OverloadedStrings #-}

module Lib.Pandoc (articleCompiler) where

import Hakyll
import Text.Pandoc.Options
import System.FilePath (takeDirectory)

-- Additional extensions for pandoc
pandocReaderExtensions :: Extensions
pandocReaderExtensions = extensionsFromList
  [ Ext_mark
  , Ext_footnotes
  , Ext_inline_notes
  , Ext_tex_math_dollars
  , Ext_citations
  , Ext_fenced_divs
  ]

-- Enhance default ReaderOptions
pandocReaderOptions :: ReaderOptions
pandocReaderOptions = defaultHakyllReaderOptions
  { readerExtensions = readerExtensions defaultHakyllReaderOptions <> pandocReaderExtensions
  }

-- Enhance default WriterOptions
pandocWriterOptions :: WriterOptions
pandocWriterOptions = defaultHakyllWriterOptions
  { writerHTMLMathMethod = KaTeX ""
  }

-- Bibliographies belong to the article directory. Avoid loading citation styles
-- for articles that do not use a bibliography.
articleCompiler :: Compiler (Item String)
articleCompiler = do
  directory <- takeDirectory . toFilePath <$> getUnderlying
  bibliographies <- loadAll (fromGlob (directory ++ "/*.bib"))
  case bibliographies of
    [] -> pandocCompilerWith pandocReaderOptions pandocWriterOptions
    _ -> do
      csl <- load "assets/csl/chicago-author-date.csl"
      document <- getResourceBody >>= readPandocBiblios pandocReaderOptions csl bibliographies
      pure $ writePandocWith pandocWriterOptions document
