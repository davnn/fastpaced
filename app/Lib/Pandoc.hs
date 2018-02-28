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

-- Add TOC to WriterOptions
pandocWriterOptionsWithTOC :: WriterOptions
pandocWriterOptionsWithTOC = pandocWriterOptions {
        writerTableOfContents = True,
        writerTOCDepth = 2,
        writerTemplate = Just "\n<div class=\"toc\">\n$toc$\n</div>\n$body$"
      }

-- Conditionally compile with or without citations
writePandoc' :: ReaderOptions -> WriterOptions -> Item CSL -> [Item Biblio] -> Compiler (Item String)
writePandoc' ropt wopt _ [] =
  pandocCompilerWith ropt wopt
writePandoc' ropt wopt csl (bib:_) =
  fmap (writePandocWith wopt)
      (getResourceBody >>= readPandocBiblio ropt csl bib)

pandocCompiler' :: Compiler (Item String)
pandocCompiler' = do
  -- get the path to the current folder
  currentRoute <- (takeDirectory . toFilePath) <$> getUnderlying
  bib <- loadAll (fromGlob (currentRoute ++ "/*.bib"))
  csl <- load $ fromFilePath "assets/csl/ieee.csl"
  id <- getUnderlying
  toc <- getMetadataField id "toc"
  let ropt = pandocReaderOptions
  let wopt = case toc of
        Just _  -> pandocWriterOptionsWithTOC
        Nothing -> pandocWriterOptions
  writePandoc' ropt wopt csl bib
