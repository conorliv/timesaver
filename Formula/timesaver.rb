# Documentation: https://docs.brew.sh/Formula-Cookbook
#                https://rubydoc.brew.sh/Formula

class Timesaver < Formula
  include Language::Python::Virtualenv

  desc "macOS CLI tool to block distracting websites on a schedule"
  homepage "https://github.com/conorliv/timesaver"
  url "https://github.com/conorliv/timesaver/archive/refs/tags/v0.1.0.tar.gz"
  sha256 "944e0e3fe9fb8b71796135f7b6972f3fc8dbe4d0ff8db039ea38dfb3894ae809"
  license "MIT"

  depends_on "python@3.11"

  resource "click" do
    url "https://files.pythonhosted.org/packages/96/d3/f04c7bfcf5c1862a2a5b845c6b2b360488cf47af55dfa79c98f6a6bf98b5/click-8.1.7.tar.gz"
    sha256 "ca9853ad459e787e2192211578cc907e7594e294c7ccc834310722b41b9ca6de"
  end

  def install
    virtualenv_install_with_resources
  end

  def caveats
    <<~EOS
      To enable/disable blocking, you need sudo:
        sudo timesaver enable
        sudo timesaver disable

      To install the background daemon:
        timesaver install-daemon
    EOS
  end

  test do
    assert_match "TimeSaver", shell_output("#{bin}/timesaver --help")
    assert_match version.to_s, shell_output("#{bin}/timesaver --version")
  end
end
