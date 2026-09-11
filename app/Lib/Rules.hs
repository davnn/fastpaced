{-# LANGUAGE OverloadedStrings #-}

module Lib.Rules (siteRules) where

import Hakyll
import Lib.Configuration (contentSnapshot, feedConfig, siteRoot)
import Lib.Content (articlePattern, bibliographyPattern, articleAttachments)
import Lib.Context (articleCtx, errorCtx, indexCtx, feedCtx)
import Lib.Url (absoluteUrl, routeUrl)
import Lib.Pandoc (articleCompiler)

-- Every published resource has one owner. Only folders with index.md publish
-- attachments; Markdown and bibliography sources are compiler inputs.
siteRules :: Rules ()
siteRules = do
  match "index.html" $ do
    route idRoute
    compile $ do
      posts <- recentFirst =<< loadAllSnapshots articlePattern contentSnapshot
      let context = indexCtx posts
      getResourceBody
        >>= applyAsTemplate context
        >>= loadAndApplyTemplate "templates/default.html" context

  match "assets/style.css" $
    compile $ compressCssCompiler >>= compileTemplateItem >>= makeItem

  match "assets/csl/*.csl" $ compile cslCompiler
  match bibliographyPattern $ compile biblioCompiler

  match articlePattern $ do
    route (setExtension ".html")
    compile $ articleCompiler
      >>= saveSnapshot contentSnapshot
      >>= loadAndApplyTemplate "templates/article.html" articleCtx
      >>= loadAndApplyTemplate "templates/default.html" articleCtx

  match ("CNAME" .||. "assets/images/**" .||. "assets/fonts/**" .||. "assets/manifest/**") $ do
    route idRoute
    compile copyFileCompiler

  articles <- getMatches articlePattern
  match (articleAttachments articles) $ do
    route idRoute
    compile copyFileCompiler

  match "templates/**" $ compile templateBodyCompiler

  create ["404.html"] $ do
    route idRoute
    compile $ makeItem ("" :: String)
      >>= loadAndApplyTemplate "templates/default.html" errorCtx

  create ["atom.xml"] $ do
    route idRoute
    compile $ do
      articles' <- recentFirst =<< loadAllSnapshots articlePattern contentSnapshot
      feedArticles <- traverse resolveFeedUrls articles'
      renderAtom feedConfig feedCtx feedArticles

-- Resolve against the actual output route, not a guessed Markdown filename.
resolveFeedUrls :: Item String -> Compiler (Item String)
resolveFeedUrls item = do
  url <- routeUrl (itemIdentifier item)
  pure $ fmap (withUrls (absoluteUrl (siteRoot ++ url))) item
