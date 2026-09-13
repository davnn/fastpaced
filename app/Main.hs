module Main (main) where

import GHC.IO.Encoding (setLocaleEncoding, utf8)
import Hakyll (hakyll)
import Lib.Rules (siteRules)

main :: IO ()
main = do
  setLocaleEncoding utf8
  hakyll siteRules
