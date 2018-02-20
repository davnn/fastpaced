module Lib.Pandoc (pandocCompiler') where

import Hakyll
import Text.Pandoc.Options
import System.FilePath (takeDirectory)

-- Additional extensions for pandoc
pandocReaderExtensions :: Extensions
pandocReaderExtensions = extensionsFromList [Ext_footnotes, Ext_inline_notes, Ext_tex_math_dollars, Ext_citations, Ext_fenced_divs]

-- Enhance default ReaderOptions
pandocReaderOptions :: ReaderOptions
pandocReaderOptions = defaultHakyllReaderOptions {
        readerExtensions = readerExtensions defaultHakyllReaderOptions `mappend` pandocReaderExtensions
      }

-- Enhance default WriterOptions
pandocWriterOptions :: WriterOptions
pandocWriterOptions  = defaultHakyllWriterOptions {
        writerHTMLMathMethod = KaTeX ""
      }

-- Conditionally compile with or without citations
compilePandoc :: Item CSL -> [Item Biblio] -> Compiler (Item String)
compilePandoc _ [] =
  pandocCompilerWith pandocReaderOptions pandocWriterOptions
compilePandoc csl (bib:_) =
  fmap (writePandocWith pandocWriterOptions)
      (getResourceBody >>= readPandocBiblio pandocReaderOptions csl bib)

pandocCompiler' :: Compiler (Item String)
pandocCompiler' = do
  -- get the path to the current folder
  currentRoute <- (takeDirectory . toFilePath) <$> getUnderlying
  bib <- loadAll (fromGlob (currentRoute ++ "/*.bib"))
  csl <- load $ fromFilePath "assets/csl/ieee-with-url.csl"
  compilePandoc csl bib
