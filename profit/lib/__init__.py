#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2007 Troy Melhase
# Distributed under the terms of the GNU General Public License v2
# Author: Troy Melhase <troy@gci.net>

from PyQt4.QtCore import QPoint, QSettings, QSize, QVariant, Qt, SIGNAL, SLOT
from PyQt4.QtGui import QBrush, QColor, QIcon, QPixmap, QTableWidgetItem


class Signals:
    """ Contains SIGNAL attributes for easy and consistent reference.

    """
    activated = SIGNAL('activated(QSystemTrayIcon::ActivationReason)')
    clicked = SIGNAL('clicked()')
    connectedTWS = SIGNAL('connectedTWS')
    createdSeries = SIGNAL('createdSeries')
    createdTicker = SIGNAL('createdTicker')
    currentChanged = SIGNAL('currentChanged(int)')
    dataChanged = \
        SIGNAL('dataChanged(const QModelIndex &, const QModelIndex &)')
    disconnectedTWS = SIGNAL('disconnectedTWS')
    itemDoubleClicked = SIGNAL('itemDoubleClicked(QTreeWidgetItem *, int)')
    lastWindowClosed = SIGNAL('lastWindowClosed()')
    layoutChanged = SIGNAL('layoutChanged()')
    modelDoubleClicked = SIGNAL('doubleClicked (const QModelIndex &)')
    modelReset = SIGNAL('modelReset()')
    sessionCreated = SIGNAL('sessionCreated(PyQt_PyObject)')
    settingsChanged = SIGNAL('settingsChanged')
    splitterMoved = SIGNAL('splitterMoved(int, int)')
    standardItemChanged = SIGNAL('itemChanged(QStandardItem *)')
    tickerClicked = SIGNAL('tickerClicked')
    timeout = SIGNAL('timeout()')
    triggered = SIGNAL('triggered()')


class Slots:
    """ Contains SLOT attributes for easy and consistent reference.

    """
    scrollToBottom = SLOT('scrollToBottom()')
    expandItem = SLOT('expandItem(const QTreeWidgetItem *)')


class Settings(QSettings):
    """ Convenient replacement for QSettings.

    """
    class keys:
        """ Attributes are setting keys.

        """
        account = 'Account'
        app = 'Profit Device'
        appearance = 'Appearance'
        main = 'MainWindow'
        maximized = 'Maximized'
        org = 'ProfitPy'
        plots = 'Plots'
        position = 'Position'
        session = 'Session'
        size = 'Size'
        strategy = 'Strategy'
        winstate = 'Window State'

    defaultSize = QSize(400, 400)
    defaultPosition = QPoint(200, 200)

    def __init__(self):
        """ Constructor.

        """
        QSettings.__init__(self, self.keys.org, self.keys.app)

    def setValue(self, key, value):
        """ Sets value of setting

        @param key setting key as string
        @param value anything supported by QVariant constructor
        @return None
        """
        QSettings.setValue(self, key, QVariant(value))

    def value(self, key, default=None):
        """ Returns value for key, or default if key doesn't exist.

        @param key setting key as string
        @param default value returned if key does not exist
        @return value of key or default
        """
        if default is None:
            default = QVariant()
        else:
            default = QVariant(default)
        return QSettings.value(self, key, default)


def importName(name):
    """ import and return a module by name in dotted form

    Copied from the Python lib docs.

    @param name module name as string
    @return module object
    """
    mod = __import__(name)
    for comp in name.split('.')[1:]:
        mod = getattr(mod, comp)
    return mod


def importItem(name):
    """ import an item from a module by dotted name

    @param name module and attribute string, i.e., foo.bar.baz
    @return value of name from module
    """
    names = name.split('.')
    modname, itemname = names[0:-1], names[-1]
    mod = importName(str.join('.', modname))
    return getattr(mod, itemname)


##
tickerIdRole = Qt.UserRole + 32


##
valueAlign = Qt.AlignRight | Qt.AlignVCenter

class ValueColorItem(object):
    increase = QBrush(QColor(Qt.darkGreen))
    neutral = QBrush(QColor(Qt.blue))
    decrease = QBrush(QColor(Qt.red))

    @classmethod
    def setColors(cls, increase, neutral, decrease):
        cls.increase = QBrush(increase)
        cls.neutral = QBrush(neutral)
        cls.decrease = QBrush(decrease)


class ValueTableItem(QTableWidgetItem, ValueColorItem):
    """ Table item that changes colors based on value changes.

    """
    def __init__(self):
        """ Constructor.

        """
        QTableWidgetItem.__init__(self, self.UserType)
        self.setFlags(self.flags() & ~Qt.ItemIsEditable)
        self.value = None

    def setValue(self, value):
        """ Sets value of item and updates text color (if possible).

        @param string or number to set
        @return None
        """
        try:
            value = float(value)
        except (ValueError, ):
            self.setText(value)
            return
        current = self.value
        if current is None:
            self.value = value
            self.setText(str(value))
            return
        if value < current:
            self.setForeground(self.decrease)
        elif value > current:
            self.setForeground(self.increase)
        else:
            self.setForeground(self.neutral)
        self.value = value
        self.setText(str(value))

    def setSymbol(self, symbol):
        """ Sets the text and icon for a symbol-based item.

        @param symbol ticker symbol as string
        @return None
        """
        icon = symbolIcon(symbol)
        self.setIcon(icon)
        self.setText(symbol)

    def setValueAlign(self, alignment=valueAlign):
        """ Sets the text alignment of this item.

        @param alignment Qt alignment flags
        @return None
        """
        self.setTextAlignment(alignment)

    def setText(self, text):
        QTableWidgetItem.setText(self, str(text))


def colorIcon(color, width=10, height=10):
    """ Creates an icon filled with specified color.

    @param color QColor instance
    @param width width of icon in pixels
    @param height of icon in pixels
    @return QIcon instance
    """
    pixmap = QPixmap(width, height)
    pixmap.fill(color)
    return QIcon(pixmap)


def symbolIcon(symbol):
    """ Icon for a symbol.

    @param symbol name of symbol
    @return QIcon instance; transparent but valid if symbol icon not found
    """
    icon = QIcon(':images/tickers/%s.png' % (symbol.lower(), ))
    if icon.pixmap(16,16).isNull():
        pixmap = QPixmap(16, 16)
        pixmap.fill(QColor(0, 0, 0, 0))
        icon = QIcon(pixmap)
    return icon


##
# Set for the nogc function/function decorator.
extra_references = set()


def nogc(obj):
    """ Prevents garbage collection. Usable as a decorator.

    @param obj any object
    @return obj
    """
    extra_references.add(obj)
    return obj


def disabledUpdates(name):
    """ Creates decorator to wrap table access with setUpdatesEnabled calls.

    @param name name of table attribute
    @return decorator function
    """
    def disableDeco(meth):
        """ Wraps method with table update disable-enable calls.

        @param meth method to wrap
        @return replacement method
        """
        def method(self, *a, **b):
            table = getattr(self, name)
            table.setUpdatesEnabled(False)
            try:
                meth(self, *a, **b)
            finally:
                table.setUpdatesEnabled(True)
        return method
    return disableDeco


def nameIn(*names):
    def check(obj):
        try:
            return obj.typeName in names
        except (AttributeError, ):
            return False
    return check
