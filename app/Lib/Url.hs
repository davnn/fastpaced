module Lib.Url (routeUrl, absoluteUrl) where

import Hakyll (Compiler, Identifier, getRoute, toFilePath, toUrl)
import Network.URI (escapeURIString, isAllowedInURI, parseURIReference, relativeTo)
import System.FilePath.Posix (takeDirectory, takeFileName)

-- Hakyll toUrl already encodes path characters; do not escape its output again.
-- File paths are URL paths, regardless of the build host's platform.
pageUrl :: FilePath -> String
pageUrl path = case takeFileName path of
  "index.html" ->
    let directory = takeDirectory path
    in if directory == "." then "/" else toUrl directory ++ "/"
  _ -> toUrl path

-- All consumers use the registered Hakyll route, including feed snapshots.
routeUrl :: Identifier -> Compiler String
routeUrl identifier = do
  pageRoute <- getRoute identifier
  maybe (fail (toFilePath identifier ++ ": missing page route")) (pure . pageUrl) pageRoute

-- RFC URI resolution handles fragments, queries, ../ and protocol-relative URLs.
absoluteUrl :: String -> String -> String
absoluteUrl base reference =
  case (parseURIReference base, parseURIReference (escapeURIString isAllowedInURI reference)) of
    (Just baseUri, Just referenceUri) -> show (referenceUri `relativeTo` baseUri)
    _ -> reference
